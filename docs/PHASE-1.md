# Phase 1 — Foundation

## Done

- Monorepo structure
- Next.js App Router + TypeScript
- MUI theme and polished starter shell
- FastAPI application
- PostgreSQL
- SQLAlchemy 2
- Alembic migration
- Organization + membership model
- User model
- Refresh token persistence
- Argon2 password hashing
- JWT access and refresh tokens
- HttpOnly authentication cookies
- CSRF token/header protection
- Basic RBAC dependency
- CORS allowlist
- Security headers
- Docker Compose
- Health/readiness endpoints

## Deliberate omissions

AI screening, resumes, jobs, applications, queues, embeddings and LLM integrations are not in Phase 1. Keeping those out prevents the foundation from becoming tightly coupled to the future screening pipeline.

## Phase 2 target

Introduce:

1. Job
2. Candidate
3. Resume
4. Application
5. Secure file upload
6. PDF/DOCX extraction
7. Organization-scoped repositories
8. Async application processing contract
