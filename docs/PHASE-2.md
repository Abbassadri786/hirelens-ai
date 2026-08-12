# Phase 2 — Recruitment Domain + Secure Resume Ingestion

This is an overlay for the working Phase 1 project. Copy these files into the same paths in your existing repo.

## Added
- Job + JobRequirement
- Candidate
- Resume
- Application + lifecycle status
- Public job board
- Recruiter job APIs
- Public application API
- PDF/DOCX extraction
- 10 MB upload limit
- extension + MIME + magic-byte checks
- UUID storage filenames
- SHA-256 file hash
- organization-scoped queries
- duplicate application protection

## Required Phase 1 auth patch
Replace the existing `csrf()` function in `backend/app/api/v1/auth.py` with:

```python
@router.get('/csrf')
def csrf(response: Response):
    import secrets
    from app.core.security import CSRF_COOKIE
    token = secrets.token_urlsafe(32)
    response.set_cookie(CSRF_COOKIE, token, max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60, httponly=False, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE, domain=settings.COOKIE_DOMAIN, path='/')
    return {'message': 'CSRF token initialized'}
```

## Run
Copy overlay files into Phase 1, then:

```bash
docker compose down
docker compose up --build
```

The Phase 1 startup command automatically executes Alembic, applying migration `0002_recruitment_domain`.

## Test
1. `/dashboard/jobs` → create job.
2. Click Publish.
3. `/jobs` → open role.
4. Upload a synthetic PDF/DOCX.
5. Submit.
6. Swagger → `GET /api/v1/applications` to review it.

## Production hardening still required
Use private object storage, signed URLs, malware scanning and an isolated parser worker before handling real candidate resumes.

## Phase 3
LangGraph screening workflow, PII redaction, deterministic skill matching, local embeddings, semantic similarity, hybrid score, Gemini/Groq provider abstraction and explainable screening results.
