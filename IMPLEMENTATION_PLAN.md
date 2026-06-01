# Quiz Platform — Implementation Plan

> Status: **Draft for approval** · Companion to `FEATURE_REQUIREMENTS.md` · Date: 2026-05-31
> No application code written yet. This plan defines *how* we build what the requirements describe.

---

## 1. Architecture at a glance

```
┌─────────────────┐      HTTP/JSON (JWT)      ┌────────────────────┐
│  React SPA      │ ────────────────────────> │  Django + DRF API  │
│  (Vite, JS)     │ <──────────────────────── │  (gunicorn)        │
│  nginx :5173    │                           │  :8000             │
└─────────────────┘                           └─────────┬──────────┘
                                                         │
                                          ┌──────────────┴───────────┐
                                          │  MySQL 8  │  media volume │
                                          │  :3306    │  (uploads)    │
                                          └───────────────────────────┘
```

Three Docker Compose services: `db` (MySQL 8), `backend` (Django/DRF), `frontend` (Vite dev server, or nginx static in prod profile). Uploaded images live on a named volume mounted into the backend.

---

## 2. Repository layout

```
instawork/
├─ FEATURE_REQUIREMENTS.md
├─ IMPLEMENTATION_PLAN.md
├─ README.md                      # build/run/test docs (deliverable)
├─ docker-compose.yml
├─ .env.example                   # DB creds, SECRET_KEY, QUIZ_LENGTH, etc.
│
├─ backend/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ manage.py
│  ├─ config/                     # project: settings, urls, wsgi
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ wsgi.py
│  ├─ accounts/                   # custom user + auth
│  ├─ questions/                  # question bank + admin CRUD
│  ├─ quiz/                       # attempts, grading, review
│  └─ tests/                      # or per-app tests
│
└─ frontend/
   ├─ Dockerfile
   ├─ package.json
   ├─ vite.config.js
   ├─ index.html
   └─ src/
      ├─ api/                     # axios client, endpoints, auth interceptor
      ├─ auth/                    # context, login/register, route guards
      ├─ admin/                   # question bank CRUD + review queue
      ├─ player/                  # start quiz, answer, submit
      ├─ results/                 # results + review + history
      ├─ components/              # shared a11y form controls
      └─ App.jsx / main.jsx
```

---

## 3. Backend

### 3.1 Stack & key dependencies
- Django 5.x, djangorestframework
- `djangorestframework-simplejwt` (JWT auth — D2)
- `mysqlclient` (MySQL driver — D8)
- `Pillow` (image validation/storage)
- `django-cors-headers` (SPA on a different origin)
- `django-filter` (list filtering: category/difficulty/type)
- Dev/test: `pytest-django` + `factory_boy` (or Django's `TestCase` — see §7)

### 3.2 Apps & models

**`accounts`**
- Custom `User` (extends `AbstractUser`) with `role` field: `admin | user`. Admins also flagged `is_staff` for Django admin access.
- Roles drive DRF permissions (see §3.4).

**`questions`**
- `Question`: `type` (`text|single|multiple|numerical|image`), `prompt`, `category`, `difficulty` (`easy|med|hard`), `is_active`, `created_by`, timestamps.
  - Type-specific fields: `accepted_text` (text), `numeric_answer` (numerical, DecimalField), `image_requirement` (image).
- `Choice`: `question` FK, `text`, `is_correct`, `order` (for `single`/`multiple`).

**`quiz`**
- `Attempt`: `user` FK, `created_at`, `submitted_at`, `score` (int, null until graded), `max_score`, `status` (`in_progress|submitted|awaiting_review|graded`).
- `AttemptQuestion`: `attempt` FK, `question` FK, `order`, **frozen snapshot** of prompt + choices (JSON) so later edits/deletes don't alter history (requirements §4).
- `Answer`: `attempt_question` FK, `text_value`, `numeric_value`, `selected_choice_ids` (JSON), `image` (FileField), `is_correct` (nullable for pending image), `reviewed_by`, `reviewed_at`.

> Migrations: one initial migration per app. MySQL note — use `utf8mb4`; `JSONField` is supported on MySQL 8.

### 3.3 Validation (server-side, in serializers + model `clean`)
Enforce per requirements §3:
- `single`: exactly one `Choice.is_correct == True`, ≥2 choices.
- `multiple`: ≥1 correct, ≥2 choices.
- `numerical`: `numeric_answer` required.
- `text`: `accepted_text` non-empty.
- `image`: `prompt`/`image_requirement` present; upload constraints (type in jpg/png/webp, ≤5 MB, 1 file) validated on answer submit.
Invalid payloads → `400` with field errors (mirrored client-side).

### 3.4 Auth & permissions
- JWT obtain/refresh via SimpleJWT.
- `IsAdminRole` permission for write operations on `questions` and all `review` endpoints.
- `IsOwner` permission so a user only reads/submits their own attempts.
- Questions are readable by authenticated users (the player needs prompts/choices — but **correct answers are never serialized to players**; a separate admin serializer exposes `is_correct`).

### 3.5 Grading engine (`quiz/grading.py`)
Pure functions, unit-tested in isolation:
- `single`: selected == the one correct id.
- `multiple`: set(selected) == set(correct) — **all-or-nothing** (D7).
- `numerical`: `Decimal(answer) == numeric_answer` — **exact** (D5).
- `text`: `normalize(answer) == normalize(accepted_text)` where normalize = trim + casefold — **single normalized** (D6).
- `image`: returns `pending` (no auto-grade); requires manual review (D4).

On submit: grade all auto types immediately, sum correct → `score`. If any image answers exist → `status = awaiting_review` and score is provisional; else `status = graded`. Admin review of an image finalizes `is_correct`, recomputes score, and flips to `graded` once no pending items remain.

### 3.6 Attempt creation / randomization
- `POST /api/attempts`: sample `QUIZ_LENGTH` (default 10, from env — D1) active questions **without replacement** (`order_by('?')[:N]` or random-id sampling for MySQL performance), snapshot each into `AttemptQuestion`. No repeats within an attempt; independent per attempt. If pool < N, serve what exists and include a notice in the response.

### 3.7 Endpoints
Per requirements §8 — auth, questions CRUD, attempts (start/submit/list/detail), review queue + verdict. `django-filter` adds `?category=&difficulty=&type=` to the questions list.

### 3.8 Seed command (`questions/management/commands/seed_questions.py`)
- Idempotent (`get_or_create` keyed on prompt). Populates **≥20 questions** spanning all 5 types and a mix of categories/difficulties. Also creates a demo admin + demo user (documented in README).

---

## 4. Frontend (React + Vite + JS)

### 4.1 Libraries
- `react-router-dom` (routing + guards)
- `axios` (client with JWT interceptor + refresh-on-401)
- `@tanstack/react-query` (server state, caching, mutations)
- Light styling: CSS modules or a small system (no heavy UI kit) to keep a11y control explicit.

### 4.2 Routes
| Route | View | Guard |
|-------|------|-------|
| `/login`, `/register` | Auth forms | public |
| `/` | Dashboard (start quiz, recent attempts) | user |
| `/quiz/:attemptId` | Player (answer + submit) | owner |
| `/results/:attemptId` | Results + review | owner/admin |
| `/history` | All past attempts | user |
| `/admin/questions` | Bank list + CRUD | admin |
| `/admin/questions/new`, `/:id/edit` | Question editor (type-aware form) | admin |
| `/admin/review` | Image review queue | admin |

### 4.3 Key components
- **Type-aware question editor**: switches fields by type; mirrors server validation (exactly-one / at-least-one correct, etc.).
- **Player question renderers**: radio group (single), checkbox group (multiple), number input (numerical), textarea (text), file input + preview (image).
- **Results view**: ✅/❌/⏳pending per question; review panel shows prompt, user answer, correct answer(s) where applicable; image items show submitted image + verdict.

### 4.4 Accessibility (NFR)
Native `<fieldset>/<legend>` for choice groups, `<label>` bound to every input, visible focus rings, keyboard-navigable flows, ARIA live region for submit/grading feedback, semantic landmarks. Manual keyboard + screen-reader smoke pass before sign-off.

---

## 5. Docker & configuration
- `docker-compose.yml`: `db` (MySQL 8, healthcheck, named volume), `backend` (waits for db health, runs migrate + optional seed, then gunicorn), `frontend` (Vite dev, or nginx in a `prod` profile).
- `.env.example` documents: `SECRET_KEY`, `DEBUG`, `MYSQL_*`, `QUIZ_LENGTH`, `CORS_ALLOWED_ORIGINS`, JWT lifetimes.
- One-command up: `docker compose up --build`; README documents seeding + creating an admin.
- Local-dev fallback documented (venv + `mysqlclient`, npm) for reviewers who skip Docker.

---

## 6. Documentation deliverables (README)
Architecture overview · one-command Docker run · local-dev fallback · create-admin + run-seed · run tests (backend + frontend) · API endpoint list with example requests · **AI-tools & novel-techniques note** (per the brief).

---

## 7. Testing strategy
**Backend (priority — pytest-django):**
- Grading unit tests for all 5 types (incl. all-or-nothing, exact numeric, normalized text, image→pending).
- Validation tests (single=exactly one, multiple≥1, required fields).
- Randomization: N served, no repeats within an attempt, independence across attempts, pool < N handled.
- Ownership/permissions: user can't read others' attempts; non-admin can't write questions or review.
- Submit→score→review flow incl. provisional → graded transition.

**Frontend (lighter):** component/smoke tests (Vitest + Testing Library) for login, start→answer→submit, results render, admin editor validation.

---

## 8. Build sequence (milestones)

1. **Scaffold + Docker** — repo layout, compose (db/backend/frontend), settings wired to MySQL, health check end-to-end.
2. **Accounts + auth** — custom user/roles, JWT endpoints, SPA login/register + guards.
3. **Question bank** — models, validation, admin serializers/endpoints, React CRUD editor; Django admin enabled.
4. **Seed command** — ≥20 questions all types + demo users.
5. **Quiz player** — attempt creation/randomization/snapshot, player UI, submit.
6. **Grading + results** — grading engine, results/review view, attempt history.
7. **Image review** — upload handling, admin review queue, score finalization.
8. **A11y + responsive pass** — keyboard/labels/focus, mobile layout.
9. **Tests + docs** — backend test suite, frontend smoke tests, README + AI-tools note.
10. **Polish** — error states, empty states, final review.

> Each milestone is independently demoable. Suggest sequential build with a working app at every step.

---

## 9. Risks / watch-items
- **MySQL random sampling** (`order_by('?')`) is fine at seed scale; note it doesn't scale to huge banks (acceptable here).
- **Image storage in Docker** — must be a persistent volume, not container FS, or uploads vanish on rebuild.
- **JWT refresh UX** — axios interceptor must handle 401→refresh→retry cleanly to avoid logout churn.
- **Snapshot vs. live questions** — results/review must read from `AttemptQuestion` snapshot, never the live `Question`.

---

### Next step
On approval, begin **Milestone 1 (scaffold + Docker)** and proceed sequentially, keeping the app runnable at each milestone.
