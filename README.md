# Irregular Verb Practice MVP

Small full-stack MVP for practicing English irregular verbs.

Intentionally does not implement the full solution from the prompt. Focuses on an end-to-end tracer bullet with an MVP approach.
The modular structure allows for extensibility, so additional question types, reports etc. are easy additions.
Online/offline modes are handled through a provider, with the offline mode seeded with example questions so there will always be content.
Dockerised for portability.

## Scope Tradeoffs

- No authentication or user accounts - anonymous cookie/session identity
- Single exercise type only (`fill_blank`)
- Minimal UI styling
- SQLite without migrations/infra tooling
- Both backend & frontend declare their own schemas - sharing types through the OpenAPI schema would be a sensible extension

## Stack

- Frontend: Svelte + Vite (`frontend`)
- Backend: FastAPI + SQLAlchemy (`backend`)
- Persistence: SQLite
- AI providers:
  - `StubAIProvider` (deterministic, no network)
  - `RealAIProvider` (LLM-backed, enabled via API key)

## Implemented Scope

- Single exercise type: `fill_blank`
- Difficulty levels 1-3
- Anonymous identity only:
  - UUID stored in cookie
  - Frontend fallback in `sessionStorage` via `X-Anonymous-Id` header
- Practice flow:
  - Generate exercise
  - Submit answer
  - Receive correctness, corrected answer, short explanation
- Generated exercises store the expected answer server-side only (not returned to clients).
- Attempt evaluation uses AI with structured JSON validation and automatic fallback to deterministic exact-match grading when AI evaluation fails.
- Progress view:
  - Overall attempts
  - Correct answers
  - Success rate
  - Success by difficulty
  - Recent attempts
- Seeded question bank (25 deterministic records) in SQLite

## Setup

From the project root, copy the example env file and paste in your OpenAI key:

```bash
cp .env.example .env
```

`LLM_API_KEY` is the only variable you need to set. Everything else has a sensible default in `backend/app/core/config.py`, so setup is just copy → paste key → run.

Provider selection:

- Key present: live LLM-generated exercises and AI grading (`RealAIProvider`).
- Key missing/empty: deterministic seed-bank questions and exact-match grading (`StubAIProvider`).

On startup the backend logs which provider mode it selected and why.

## Run Anywhere (Recommended)

From project root:

```bash
docker compose up --build
```

Services:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

This path avoids local Python/Node version drift.

## Local Dev (No Docker)

From project root:

```bash
npm run dev
```

This script:

1. Ensures frontend dependencies are installed
2. Ensures backend dependencies are installed
3. Seeds SQLite question bank
4. Starts backend and frontend

## Tests

Backend:

```bash
cd backend
python -m pytest
```

Frontend checks:

```bash
cd frontend
npm ci
npm run check
```

## CI

GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

- Backend tests
- Frontend type/Svelte checks

## API Endpoints

- `POST /api/session`
- `POST /api/exercise`
- `POST /api/attempt`
- `GET /api/progress`