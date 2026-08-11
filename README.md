# HireLens AI — Phase 1

AI-powered recruitment screening platform foundation.

Phase 1 focuses on the production-style foundation:
- Next.js + TypeScript + MUI frontend
- FastAPI backend
- PostgreSQL database
- SQLAlchemy 2 ORM + Alembic
- Argon2id password hashing
- JWT access/refresh tokens in HttpOnly cookies
- CSRF protection for authenticated state-changing requests
- RBAC: organization admin, recruiter, hiring manager, candidate
- Multi-tenant organization model
- Docker Compose local development
- Health/readiness endpoints
- Structured project boundaries for later AI screening work

## Architecture

Browser → Next.js → FastAPI → PostgreSQL

Future phases add:
FastAPI → screening queue → LangGraph → Gemini/Groq/local embeddings → screening results

## Prerequisites

- Docker Desktop
- Node.js 20+
- Python 3.12+ if running the backend outside Docker

## Quick start

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend:
http://localhost:3000

API:
http://localhost:8000

Swagger:
http://localhost:8000/docs

## Local development without Docker

Backend:

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

Never commit `backend/.env`.

Use `backend/.env.example` as the template.

## Phase 1 API

- POST `/api/v1/auth/register`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`
- GET `/api/v1/auth/csrf`
- GET `/api/v1/auth/me`
- GET `/api/v1/organizations/me`
- GET `/api/v1/health`
- GET `/api/v1/ready`

## Security notes

Passwords are hashed with Argon2id using pwdlib, following FastAPI's current security guidance. JWTs are not stored in localStorage; they are issued through HttpOnly cookies. Authenticated state-changing requests require a CSRF header matching a CSRF cookie.

The current cookie configuration is suitable for local development. Production deployment should set HTTPS-only cookies and a production frontend origin.

## Phase 2

Resume ingestion, secure PDF/DOCX parsing, candidate/job models, application workflow, and asynchronous screening pipeline.
