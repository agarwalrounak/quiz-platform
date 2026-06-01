# Quiz Platform — Feature Requirements

> Status: **Draft for approval** · Owner: rounak@weekday.works · Date: 2026-05-31
> No code has been written yet. This document defines scope before implementation.

---

## 1. Overview

A small but complete quiz platform with three surfaces:

1. **Admin** — manage a question bank (full CRUD) across five question types.
2. **Quiz Player** — end users take an attempt of N randomized questions, submit answers, and get scored.
3. **Results & History** — per-attempt results with review, plus a list of all of a user's past attempts.

Backend: Django + DRF · Frontend: React + Vite (JavaScript) · DB: MySQL · Orchestration: Docker Compose.

Backend is **Django + Django REST Framework**. Frontend is a **React + Vite + JavaScript** SPA. Data persists in **MySQL**. The whole stack runs via **Docker Compose**.

---

## 2. Decisions locked with stakeholder

These resolve ambiguities (and one contradiction) in the original brief.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| D1 | **Quiz length** | **Configurable**, default **10** questions/attempt. Score is `0–N` where N = quiz length. | Brief contradicted itself ("10" in intro vs "5" / "0–5" in player section). A setting satisfies both and is more flexible. |
| D2 | **Auth** | **DRF + JWT.** Two roles: `admin` (manages bank) and `user` (takes quizzes). | "Users access all their previous attempts" requires real identity; JWT is SPA-idiomatic. |
| D3 | **Frontend** | **React + Vite + JavaScript.** | Strong ecosystem, easy to demo, less boilerplate. |
| D4 | **Text/Image grading** | **Hybrid.** Text auto-graded by normalized match (instant). Image stored and flagged for **manual admin review**; attempt shows status `pending` for those items until reviewed. | Deterministic where possible; human-in-the-loop where grading is genuinely subjective. |
| D5 | **Numerical grading** | **Exact match only.** | Simple, unambiguous. |
| D6 | **Text matching** | **Single accepted answer**, normalized: case-insensitive + trimmed whitespace. | Predictable; avoids fuzzy-match false positives. |
| D7 | **Multiple-choice scoring** | **All-or-nothing.** Full credit only if selected set exactly equals correct set. | Keeps score an integer `0–N`; no fractional credit. |
| D8 | **Packaging** | **Docker Compose** (Django + MySQL + frontend) with one-command setup. | Easiest for a reviewer to run. |

---

## 3. Question Types

| Type | Key | User input | Grading | Admin validation |
|------|-----|-----------|---------|------------------|
| Text (free response) | `text` | Free text | Auto: normalized (case-insensitive, trimmed) equality vs single accepted answer | Accepted answer required (non-empty) |
| Single choice | `single` | One option | Auto: chosen == the one correct option | Exactly **one** option marked correct; ≥2 options total |
| Multiple choice | `multiple` | One or more options | Auto: selected set == correct set (all-or-nothing) | **At least one** option correct; ≥2 options total |
| Numerical input | `numerical` | A number | Auto: exact equality vs stored numeric value | Correct numeric answer required |
| Image upload | `image` | Image file | **Manual** admin review (correct/incorrect); item `pending` until reviewed | Prompt must state the requirement; upload constraints defined (type/size) |

Image upload constraints (proposed): accept `jpg/jpeg/png/webp`, max **5 MB**, one file per answer.

---

## 4. Data Model (proposed)

- **User** (Django auth user) — extended with `role` (`admin` | `user`). Admins are also Django staff for `/admin`.
- **Question**
  - `type` (one of the five), `prompt` (text), `category` (string/tag), `difficulty` (`easy|med|hard`)
  - `accepted_text` (for text), `numeric_answer` (for numerical), `image_requirement` (for image)
  - `is_active` (soft-delete / exclude from pool), timestamps, `created_by`
- **Choice** (for `single`/`multiple`) — `question` FK, `text`, `is_correct`, `order`
- **Attempt** — `user` FK, `created_at`, `submitted_at`, `score` (int, nullable until graded), `max_score` (= N), `status` (`in_progress` | `submitted` | `awaiting_review` | `graded`)
- **AttemptQuestion** — snapshot link of `attempt` → `question` (preserves the exact question/choices served, ordered). Prevents later edits from corrupting past attempts.
- **Answer** — `attempt_question` FK, payload per type (`text_value`, `numeric_value`, `selected_choice_ids`, `image` file), `is_correct` (nullable for pending image), `reviewed_by`, `reviewed_at`.

> **Snapshotting** (AttemptQuestion + frozen choices) is a deliberate addition beyond the brief: editing or deleting a question later must not change what a historical attempt showed or scored.

---

## 5. Admin (Question Bank)

- **CRUD** on questions via DRF API + a usable admin UI (React admin screens; Django admin also available as a fallback/power tool).
- **Tagging**: every question has `category` (free text/select) and `difficulty` (`easy|med|hard`).
- **Validation** enforced server-side (and mirrored client-side) per the table in §3. Invalid questions cannot be saved.
- **Image review queue**: list of submitted image answers awaiting grading; admin marks each correct/incorrect, which finalizes the affected attempt's score and flips its status to `graded`.
- **Bulk seed**: a management command (`manage.py seed_questions`) populating **≥20 questions** covering **all five types** and a spread of categories/difficulties. Idempotent (safe to re-run).

---

## 6. Quiz Player (User)

- **Start attempt** → server selects **N random** questions (default 10) from the active pool.
  - Independently randomized per attempt; **no repeats within an attempt** (sampling without replacement).
  - If the pool has fewer than N active questions, serve as many as exist and log/inform.
- **Answer & submit**:
  - Single/multiple/numerical/text auto-graded immediately on submit.
  - Image answers stored → attempt status becomes `awaiting_review` if any image items exist; otherwise `graded` immediately.
- **Navigation**: move between questions, see answered/unanswered state, submit the attempt.

---

## 7. Results & Review

- **Score**: overall `score / max_score` (0–N). If image items are pending, show provisional score + clear "awaiting review" indicator.
- **Per-question correctness**: ✅ / ❌ (and a `pending` state for un-reviewed images).
- **Review mode**: for each question show the prompt, the user's answer, and the correct answer(s) where applicable (text/single/multiple/numerical). For image items, show the submitted image + reviewer verdict.
- **Attempt history**: a user can list and open **all their previous attempts** with score, date, and status.

---

## 8. API Surface (indicative)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/auth/register` | Register user | public |
| POST | `/api/auth/login` | Obtain JWT | public |
| POST | `/api/auth/refresh` | Refresh JWT | token |
| GET/POST | `/api/questions` | List / create questions | user(read) / admin(write) |
| GET/PUT/PATCH/DELETE | `/api/questions/{id}` | Retrieve / update / delete | admin (write) |
| POST | `/api/attempts` | Start attempt (returns N random questions) | user |
| POST | `/api/attempts/{id}/submit` | Submit answers, trigger grading | user (owner) |
| GET | `/api/attempts` | List own attempts (history) | user |
| GET | `/api/attempts/{id}` | Attempt detail + review data | user (owner) / admin |
| GET | `/api/review/queue` | Pending image answers | admin |
| POST | `/api/review/answers/{id}` | Mark image answer correct/incorrect | admin |

Ownership enforced: a user can only read/submit their own attempts.

---

## 9. Non-functional Requirements

- **Accessibility**: full keyboard navigation, proper form `label`s/ARIA, visible focus states, semantic landmarks. Radio (single) and checkbox (multiple) groups use native inputs.
- **Responsive**: works on mobile and desktop (single-column on small screens).
- **Persistency**: MySQL for all data; uploaded images on a file-backed media volume. No in-memory-only state.
- **Security**: JWT auth, role checks on every admin/owner endpoint, file-type/size validation on uploads.
- **Testing**: backend unit/integration tests for grading logic, validation rules, randomization (no repeats, independence), and ownership. Frontend has at least smoke/component tests for the core flows.

---

## 10. Documentation Deliverables

- **README**: architecture overview, one-command Docker run, local-dev fallback, how to create an admin, how to run the seed command, how to run tests.
- **API notes**: endpoint list + example requests.
- **This requirements doc** kept current.
- **AI-tools note**: a short section disclosing AI assistance and any novel techniques used (per the brief's request).

---

## 11. Out of Scope (proposed)

- Timed quizzes / countdown.
- Leaderboards / social features.
- Email verification / password reset flows.
- LLM-based grading (considered for text/image; deferred — deterministic + manual review chosen instead).
- Question import from CSV/file (seed script covers population).

> If any of these should move **in** scope, flag it and I'll revise.

---

## 12. Open Questions / Assumptions

- A1: Admin accounts are created via Django `createsuperuser` / management command (no public admin signup).
- A2: One image file per image-type answer is sufficient.
- A3: Default quiz length is 10; the value lives in settings/env and is read at attempt-start.
- A4: Categories are free-form strings (not a managed taxonomy) for v1.

---

### Next step

On approval of this document I'll produce an implementation plan (project layout, models, endpoints, seed data, tests, Docker) — still before writing code.
