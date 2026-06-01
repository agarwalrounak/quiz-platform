# Quiz Platform

A small quiz platform: an admin question bank, a quiz player that serves randomized
attempts, automatic + manual grading, results, and per-user attempt history.

- **Backend:** Django + Django REST Framework
- **Frontend:** React + Vite (JavaScript)
- **Database:** MySQL 8
- **Orchestration:** Docker Compose

See [`FEATURE_REQUIREMENTS.md`](FEATURE_REQUIREMENTS.md) and
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) for scope and design.

> **Build status:** Milestones 1–6 complete (scaffold + Docker; JWT auth with
> roles; question bank + admin editor; seed; quiz player with randomized
> attempts, snapshotting, auto-grading, and image uploads; results + review
> screen and attempt history). The admin image-review queue lands next.

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
- **Django admin:** http://localhost:8000/admin/ (create an admin first, below).

Create an admin user (superusers automatically get the `admin` role):

```bash
docker compose exec backend python manage.py createsuperuser
```

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
Questions are also manageable via Django admin at `/admin/`.

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
# Backend
cd backend && python manage.py test        # (test suite grows with each milestone)

# Frontend
cd frontend && npm test
```

---

## Configuration

All configuration is environment-driven; see [`.env.example`](.env.example).
Key variables: `QUIZ_LENGTH` (questions per attempt, default 10), MySQL credentials,
JWT lifetimes, and `CORS_ALLOWED_ORIGINS`.

---

## AI tools & techniques

This project is being built with AI assistance (Claude Code). Notable techniques and
disclosures will be documented here as the build progresses.
