# Apply Phase 3 + Phase 4

This ZIP is an overlay for your existing Phase 2 project. Keep your Phase 2 folder and Git history.

## 1. Backup
From project root:

```powershell
git add .
git commit -m "chore: phase 2 stable checkpoint"
```

## 2. Extract
Extract this ZIP into the root of `hirelens-ai/` and preserve the folder structure.

## 3. Backend dependencies
From `backend`:

```powershell
.\.venv\Scripts\activate
pip install google-genai groq
```

Or add these to your existing `requirements.txt`:

```text
google-genai>=1.31,<2.0
groq>=0.31,<1.0
```

## 4. Environment
Add to `backend/.env`:

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
AI_PROVIDER_TIMEOUT_SECONDS=20
```

Gemini is optional. The deterministic screening engine works without an API key.

## 5. Migration — IMPORTANT
Do NOT touch the Phase 2 migration again.

First verify:

```powershell
alembic current
```

Expected:

```text
0002_recruitment_domain
```

Then run:

```powershell
alembic upgrade head
```

Expected:

```text
Running upgrade 0002_recruitment_domain -> 0003_ai_screening
```

### Why this migration is safe regarding the previous ENUM problem

`0003_ai_screening.py` creates **zero PostgreSQL ENUM types**.

It creates only:

- `screening_results`
- one organization index
- one unique application constraint

It does NOT call `CREATE TYPE`.
It does NOT recreate:
- `job_status`
- `resume_file_type`
- `resume_status`
- `application_status`

Those are owned by Phase 2.

## 6. Verify migration

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'screening_results';
```

## 7. Backend router
The overlay wires:

```text
/api/v1/screening
/api/v1/analytics
```

Start:

```powershell
uvicorn app.main:app --reload
```

## 8. Frontend authentication protection
The generated `AuthProvider` calls:

```text
GET /api/v1/auth/me
```

using the existing HTTP-only authentication cookie.

Public routes:
- `/signin`
- `/signup`

Everything else is treated as protected.

If a user:
- opens `/jobs` without auth
- opens `/dashboard`
- opens a screening page
- refreshes after the auth cookie expires
- directly enters a protected URL

then `/api/v1/auth/me` returns 401 and the browser is redirected to:

```text
/signin?next=<original-path>
```

This avoids storing the auth token in localStorage.

## 9. Wire AuthGate into layout
Open:

```text
frontend/src/app/layout.tsx
```

Add:

```tsx
import AuthGate from "@/components/auth/AuthGate";
```

Wrap your existing `{children}`:

```tsx
<AuthGate>
  {children}
</AuthGate>
```

Keep your existing MUI ThemeProvider and other providers.

## 10. Protect existing Jobs and Dashboard pages
The generated Phase 3/4 pages already use:

```tsx
<ProtectedRoute>
```

For your existing Phase 2 pages, wrap:

```text
/dashboard
/dashboard/jobs
/jobs
/jobs/[id]
```

with `ProtectedRoute`.

This specifically implements your requested behavior that an unauthenticated user on the Jobs page or any inner application page is sent to sign-in.

## 11. Frontend API
Do not overwrite your existing Phase 2 `frontend/src/lib/api.ts`.

The new API client is:

```text
frontend/src/lib/api-phase3-4.ts
```

The new pages import from it.

This prevents the Phase 3/4 changes from accidentally removing your Phase 1/2 auth/job/application API code.

## 12. Run frontend

```powershell
npm install
npm run dev
```

## 13. Test authentication

Sign out, then open:

```text
http://localhost:3000/jobs
http://localhost:3000/dashboard
http://localhost:3000/dashboard/screening
http://localhost:3000/dashboard/analytics
```

Each should redirect to:

```text
/signin?next=...
```

Sign in and you should be returned to the requested route.

## 14. Test AI screening

1. Sign in as recruiter.
2. Create a job.
3. Add required skills.
4. Publish it.
5. Submit a synthetic resume.
6. Open `/dashboard/screening`.
7. Click `Run AI screen`.
8. Open the result.

You should see:
- overall score
- keyword score
- semantic signal
- experience score
- completeness
- matched skills
- missing required skills
- strengths
- concerns
- explanation

## 15. Test analytics

Open:

```text
/dashboard/analytics
```

You should see:
- total jobs
- total applications
- screened applications
- average score
- screening distribution

## 16. Gemini behavior

Without `GEMINI_API_KEY`:

```text
Resume
  ↓
PII redaction
  ↓
Deterministic ATS engine
  ↓
ScreeningResult
```

With Gemini:

```text
Resume
  ↓
PII redaction
  ↓
Deterministic ATS score
  ↓
Gemini explanation
  ↓
ScreeningResult
```

The LLM does not decide the numeric score. This makes the system more explainable and testable.

## 17. Commit

```powershell
git add .
git commit -m "feat: add AI screening and recruiter analytics"
```

## Phase 3 + 4 architecture

```text
Candidate Resume
      ↓
Secure File Validation
      ↓
PDF/DOCX Parser
      ↓
PII Redaction
      ↓
Deterministic ATS Engine
      ├── Keyword Match
      ├── Experience
      ├── Completeness
      └── Semantic Signal
      ↓
Optional Gemini Explanation
      ↓
ScreeningResult
      ↓
Recruiter Screening Queue
      ↓
Analytics
```

The next phase should focus on true local embeddings/semantic similarity, asynchronous processing, provider fallback, audit logs, private object storage, and bulk screening.
