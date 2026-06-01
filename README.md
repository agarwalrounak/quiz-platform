# Quiz Platform

A small quiz platform: an admin question bank, a quiz player that serves randomized
attempts, automatic + manual grading, results, and per-user attempt history.

- **Backend:** Django + Django REST Framework
- **Frontend:** React + Vite (JavaScript)
- **Database:** MySQL 8
- **Orchestration:** Docker Compose

See [`FEATURE_REQUIREMENTS.md`](FEATURE_REQUIREMENTS.md) and
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for scope and design.

> **Build status:** Complete (Milestones 1–10) — scaffold + Docker; JWT auth
> with roles; question bank + admin editor; seed; quiz player with randomized
> attempts, snapshotting, auto-grading, and image uploads; results + review
> screen and attempt history; admin image-review queue; accessibility +
> responsive pass; test suite (42 backend + 16 frontend) + docs; and a final
> polish pass (empty/error/edge-case states).

---

## Quick start (Docker)

Prerequisites: Docker + Docker Compose.

```bash
cp .env.example .env        # adjust secrets if you like
docker compose up --build
```

Then open:

- **Frontend:** http://localhost:5173 — should show "✅ Connected".
- **Backend health:** http://localhost:8000/api/health/ — `{"status": "ok", ...}`.

### Seed demo data

Populate the bank with 24 questions (all five types, 8 categories) plus demo
accounts. The command is idempotent — safe to run repeatedly.

```bash
docker compose exec backend python manage.py seed_questions
```

Demo accounts created by the seed:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `adminpass123` | admin |
| `player1` | `s3cretpass99` | user |

You can also auto-seed on container startup by setting `SEED_ON_START=true` in `.env`.

### Auth API

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/auth/register/` | Self-register (creates a `user` role) | public |
| POST | `/api/auth/login/` | Obtain JWT pair; response includes `user` + `role` | public |
| POST | `/api/auth/refresh/` | Exchange a refresh token for a new access token | refresh token |
| GET  | `/api/auth/me/` | Current authenticated user | access token |

Example:

```bash
curl -X POST localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"player1","password":"s3cretpass99"}'

curl -X POST localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"player1","password":"s3cretpass99"}'
# -> { "access": "...", "refresh": "...", "user": {"role": "user", ...} }
```

The SPA stores tokens in `localStorage`, attaches the access token to every
request, and transparently refreshes once on a 401 before redirecting to login.
Routes are guarded by role: `/admin/*` requires the `admin` role.

### Question bank API

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/questions/` | List (filter: `?type=&category=&difficulty=&is_active=`) | any authenticated |
| POST | `/api/questions/` | Create | admin |
| GET | `/api/questions/{id}/` | Retrieve | any authenticated |
| PUT/PATCH | `/api/questions/{id}/` | Update (choices replaced wholesale) | admin |
| DELETE | `/api/questions/{id}/` | Delete | admin |

Per-type validation is enforced server-side (and mirrored in the React editor):

- **single** — exactly one correct choice, ≥2 choices
- **multiple** — ≥1 correct choice, ≥2 choices
- **numerical** — `numeric_answer` required (graded by exact match)
- **text** — `accepted_text` required (case-insensitive, trimmed match)
- **image** — `image_requirement` required (graded by manual review)

The admin question editor lives at `/admin/questions` (list + filters + delete)
and `/admin/questions/new` · `/admin/questions/:id/edit` (type-aware form).

### Quiz player API

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/attempts/` | Start an attempt — serves `QUIZ_LENGTH` random questions (no repeats, independently randomized, answers hidden) | user |
| GET | `/api/attempts/` | List the caller's own attempts (history) | owner |
| GET | `/api/attempts/{id}/` | Attempt detail (owner-scoped; 404 for others) | owner |
| POST | `/api/attempts/{id}/submit/` | Submit answers (multipart for image uploads), auto-grade, score | owner |

**Grading** (see `quiz/grading.py`): single/multiple/numerical/text are graded
automatically on submit — multiple-choice is all-or-nothing, numerical is exact,
text is normalized (case-insensitive, trimmed). Image answers are stored and
left **pending**, so an attempt containing an image becomes `awaiting_review`
with a provisional score until an admin reviews it (review queue: next milestone).

Each served question is **snapshotted** into the attempt at start time, so later
edits or deletes to the question bank never alter past attempts or their scores.

Submit accepts `multipart/form-data`: an `answers` field (JSON array of
`{attempt_question, text_value?, numeric_value?, selected_choice_ids?}`) plus
`image_<attempt_question_id>` file parts for image questions.

**Results & review.** `GET /api/attempts/{id}/` returns the player view while an
attempt is in progress (answers hidden) and switches to a **review view once
submitted** — exposing, per question, the user's answer, the correct answer(s),
and correctness (✅/❌, or ⏳ for image answers still awaiting review). The SPA
renders this at `/results/:id`; `/history` lists all of the user's attempts with
date, score, and status, linking each to its review (or resume, if unfinished).

### Admin image-review API

Image answers are graded manually. Submitting an attempt that contains an image
leaves it `awaiting_review` with a provisional score until an admin rules on it.

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/api/review/queue/` | Pending image submissions across all users (image, prompt, requirement, who/which attempt) | admin |
| POST | `/api/review/answers/{id}/` | Body `{ "is_correct": true\|false }` — records the verdict + reviewer, then recomputes the attempt's score and flips it to `graded` once nothing is pending | admin |

The SPA exposes this at `/admin/review` (image preview + Correct/Incorrect
buttons). Score finalization is centralized in `Attempt.recalculate()`, so a
verdict immediately updates the score the player sees on their results page.

Stop and remove everything (including the DB volume):

```bash
docker compose down -v
```

---

## Local development (without Docker)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # needs MySQL client libs for mysqlclient
# Quick zero-dependency run with SQLite instead of MySQL:
export DB_ENGINE=sqlite
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```

The frontend reads `VITE_API_BASE` (default `http://localhost:8000`).

---

## Testing

```bash
# Backend (Django test runner) — 42 tests
cd backend && python manage.py test
# Inside Docker:
docker compose exec backend python manage.py test

# Frontend (Vitest + Testing Library) — 16 tests
cd frontend && npm test
```

**Backend coverage** (`accounts`, `questions`, `quiz`):
- Auth: registration (incl. weak-password + privilege-escalation guards), login
  returning role, `me`, superuser→admin role.
- Question validation: single = exactly one correct, multiple ≥ 1, ≥ 2 choices,
  required numerical/text/image fields; admin-only writes; read filtering.
- Seed command: all five types present, single-choice integrity, idempotency.
- Grading engine: text (normalized), numerical (exact), single, multiple
  (all-or-nothing) — tested as pure functions.
- Attempts: N served, no repeats, independent randomization, pool < N, answers
  hidden in-progress vs. revealed after submit, owner isolation, re-submit guard.
- Image review: queue lists only pending, admin-only, verdict finalizes score
  and flips `awaiting_review` → `graded`.

**Frontend coverage**: login form a11y, question-editor validation + valid
submit, results review (score + ✅/❌ markers + revealed answers), history list +
empty state, and the quiz player (questions, progress, prompt-tied radio group).

---

## Accessibility & responsive design

The SPA is built to be keyboard-navigable and screen-reader friendly:

- **Skip link** — a "Skip to main content" link is the first focusable element.
- **Focus management** — on every route change focus moves to the main region,
  and the new page name is announced via an `aria-live` region; `document.title`
  updates per route.
- **Forms** — every input has an associated `<label>`; choice questions use
  native radio/checkbox groups inside `<fieldset>`/`<legend>`, and each group is
  tied to its question prompt with `aria-labelledby`. Errors use `role="alert"`
  and inputs flag `aria-invalid`.
- **Navigation** — current page is marked with `aria-current="page"` (and shown
  visually). Status/progress use `role="status"` / `aria-live`.
- **Visible focus** — a high-contrast focus ring on every focusable element.
- **Contrast** — body and muted text meet WCAG AA (≥ 4.5:1) on the dark theme.
- **Responsive** — single-column layouts on small screens; data tables collapse
  to stacked cards; the navbar and review queue reflow for mobile.

## Configuration

All configuration is environment-driven; see [`.env.example`](.env.example).
Key variables: `QUIZ_LENGTH` (questions per attempt, default 10), MySQL credentials,
JWT lifetimes, and `CORS_ALLOWED_ORIGINS`.

---

## AI tools & techniques

This project was built with AI assistance (Claude Code) used as a pair-programmer:
scaffolding, drafting code/tests, and running verification. Every milestone was
checked the same way — unit tests **plus** a live end-to-end run against the real
Docker + MySQL stack (curl flows for the API; build + Testing Library for the SPA)
— so each step was demonstrably working before moving on.

A few design techniques worth highlighting:

- **Answer-snapshotting for attempt integrity.** Each served question is frozen
  into an `AttemptQuestion` (prompt + choices + correct answers) when an attempt
  starts, so later edits or deletions to the question bank never alter a past
  attempt's content or score. Results/review always read the snapshot.
- **Leak-proof serialization.** Player-facing serializers never include correct
  answers; the attempt detail endpoint only switches to the answer-revealing
  "review" serializer **after** submission (`submitted_at` gate), verified by
  tests in both directions.
- **One source of truth for scoring.** `Attempt.recalculate()` centralizes score
  + status computation and is reused by both auto-grading on submit and the admin
  image verdict, so a manual review instantly and consistently updates the score
  the player sees — including the provisional → final (`awaiting_review` →
  `graded`) transition.
- **Pure grading engine.** Grading is a set of side-effect-free functions
  (`quiz/grading.py`) unit-tested in isolation from the HTTP layer.
- **SPA accessibility plumbing.** A small `RouteManager` restores the behaviors
  full-page loads give for free — moving focus to main content on navigation,
  announcing the page via `aria-live`, and setting `document.title` per route.
