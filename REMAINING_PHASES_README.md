# HireLens AI — Remaining Enterprise Phases

This ZIP is an **overlay** for the existing HireLens AI Phase 1–4 project.

It adds the remaining production-oriented capabilities without replacing the Phase 1–4 project.

## What is included

### Phase 5 — Real semantic matching
- Local `sentence-transformers`
- `all-MiniLM-L6-v2`
- Cosine similarity
- No resume text needs to be sent to an embedding SaaS
- `screening_service_v2.py` is provided as a safe drop-in alternative

### Phase 6 — Async screening
- PostgreSQL-backed screening queue
- `QUEUED → RUNNING → COMPLETED/FAILED`
- Retry count
- Backoff
- Bulk enqueue by job
- Worker process

### Phase 7 — Enterprise observability
- Audit event model
- Screening queue metrics
- Audit dashboard
- Request trace fields
- Bias/protected-attribute hint detection

### Phase 8 — Production foundations
- Authentication bug fix
- HTTP status-aware frontend API errors
- Worker Dockerfile
- Compose file
- Tests
- Operational dashboard

## Important hiring-system safety rule

The project is designed as recruiter decision support.

It MUST NOT automatically reject, hire, or rank people based on protected characteristics or proxy attributes.

The numeric ATS score is an explainable screening signal. A recruiter remains responsible for the employment decision.

---

# APPLY ORDER

## 1. Commit your current Phase 4

From the existing project root:

```powershell
git add .
git commit -m "chore: phase 4 stable checkpoint"
```

## 2. Extract this ZIP

Extract into the existing:

```text
hirelens-ai/
```

Do not create a nested `hirelens-ai/hirelens-ai`.

## 3. Install backend packages

Activate the existing virtual environment:

```powershell
cd backend
.\.venv\Scripts\activate
```

Install:

```powershell
pip install sentence-transformers numpy
```

Keep your existing FastAPI/SQLAlchemy/Alembic packages.

## 4. Migration

The migration chain is:

```text
0001_initial
    ↓
0002_recruitment_domain
    ↓
0003_ai_screening
    ↓
0004_screening_operations
    ↓
0005_screening_indexes
```

Run:

```powershell
alembic current
```

It should currently show:

```text
0003_ai_screening
```

Then:

```powershell
alembic upgrade head
```

Expected:

```text
Running upgrade 0003_ai_screening -> 0004_screening_operations
Running upgrade 0004_screening_operations -> 0005_screening_indexes
```

### ENUM safety

`0004` and `0005` create **no PostgreSQL ENUMs**.

They use ordinary `VARCHAR` fields for queue state and indexes only.

Do not edit or rerun `0002_recruitment_domain.py`.

## 5. Add model imports

`backend/app/models/__init__.py` is included in this overlay and contains:

```python
from app.models.screening_job import ScreeningJob
from app.models.audit_event import AuditEvent
```

If your existing `__init__.py` has additional models from Phase 1–4, preserve those imports too.

## 6. Wire new routers

Open:

```text
backend/app/main.py
```

Add:

```python
from app.api.v1 import audit, operations, screening_bulk
```

Then:

```python
app.include_router(audit.router, prefix="/api/v1")
app.include_router(operations.router, prefix="/api/v1")
app.include_router(screening_bulk.router, prefix="/api/v1")
```

If your `app/api/v1/__init__.py` imports modules, add the same modules there.

## 7. Authentication fix

The overlay replaces:

```text
frontend/src/components/auth/AuthProvider.tsx
frontend/src/components/auth/ProtectedRoute.tsx
frontend/src/components/auth/AuthGate.tsx
```

The provider now:

- does NOT call `/auth/me` on `/login`, `/signin`, or `/signup`
- redirects only on HTTP 401
- does NOT interpret 404 as authentication failure
- does NOT interpret 500 as authentication failure
- does NOT create an auth redirect loop
- preserves the original route using `next=...`

## 8. IMPORTANT: verify your actual login route

The included provider redirects to:

```text
/login
```

If your real authentication page is:

```text
/signin
```

change:

```typescript
const loginPath = "/login";
```

to:

```typescript
const loginPath = "/signin";
```

Keep both in:

```typescript
const PUBLIC_ROUTES = ["/login", "/signin", "/signup"];
```

## 9. Fix API error status handling

Your existing `frontend/src/lib/api.ts` must preserve HTTP status codes.

If it currently throws only:

```typescript
throw new Error("Request failed");
```

replace that behavior with an error containing:

```typescript
class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}
```

Then throw:

```typescript
throw new ApiError(
  response.status,
  body.detail ?? response.statusText ?? "Request failed"
);
```

This is necessary for:

```text
401 → redirect to login
404 → show API error
500 → show server error
```

## 10. Real embeddings

The file:

```text
backend/app/services/embeddings.py
```

uses:

```text
all-MiniLM-L6-v2
```

The first execution downloads the model and caches it.

For the deterministic ATS engine to use real local semantic similarity, integrate:

```text
screening_service_v2.py
```

instead of the Phase 3:

```text
screening_service.py
```

The simplest approach is to rename the old implementation:

```text
screening_service.py
→ screening_service_legacy.py
```

and:

```text
screening_service_v2.py
→ screening_service.py
```

Do this only after the Phase 3 screening flow is already working.

## 11. Start worker

API:

```powershell
uvicorn app.main:app --reload
```

Worker in another terminal:

```powershell
cd backend
.\.venv\Scripts\activate
python -m app.workers.screening_worker
```

The worker continuously claims:

```text
QUEUED
```

screening jobs and processes them.

## 12. Bulk screening

After wiring `screening_bulk.router`, these endpoints exist:

```text
POST /api/v1/screening/applications/{application_id}/enqueue
POST /api/v1/screening/jobs/{job_id}/enqueue
```

The second endpoint queues every application for a job.

The API does NOT synchronously screen 1,000 resumes.

Instead:

```text
1000 applications
       ↓
1000 queue records
       ↓
worker
       ↓
screen one at a time
       ↓
results stored
```

This prevents one HTTP request from timing out while processing the entire candidate pool.

## 13. Test

Install:

```powershell
pip install pytest
```

Run:

```powershell
pytest
```

## 14. Frontend

New pages:

```text
/dashboard/operations
/dashboard/audit
```

Both are protected.

## 15. Docker worker

The included:

```text
backend/Dockerfile.worker
```

is intended for a separate worker deployment.

The worker and API should eventually be separate processes/services.

## 16. Git checkpoint

After verification:

```powershell
git add .
git commit -m "feat: complete enterprise screening pipeline"
```

---

# FINAL ARCHITECTURE

```text
                         HireLens AI
                              │
              ┌───────────────┴───────────────┐
              │                               │
          Candidate                        Recruiter
              │                               │
          Apply Job                       Dashboard
              │                               │
          Resume PDF/DOCX              Screening Queue
              │                               │
              ▼                               ▼
       Secure File Parser              Bulk Enqueue
              │                               │
              ▼                               ▼
         PII Redaction                  PostgreSQL Queue
              │                               │
              └───────────────┬───────────────┘
                              ▼
                    Screening Worker
                              │
               ┌──────────────┼──────────────┐
               │              │              │
          Keywords       Experience      Completeness
               │              │              │
               └──────────────┼──────────────┘
                              ▼
                    Local MiniLM Embedding
                              │
                              ▼
                     Semantic Similarity
                              │
                              ▼
                     Deterministic Score
                              │
                              ▼
                  Optional Gemini Explanation
                              │
                              ▼
                       Screening Result
                              │
               ┌──────────────┼──────────────┐
               │              │              │
          Recruiter       Analytics       Audit Log
               │              │              │
               └──────────────┴──────────────┘
```

## What is intentionally NOT included

This project should not use an LLM as an autonomous hiring decision maker.

Do not implement:

```text
ATS < 60 → automatically reject candidate
```

Instead:

```text
ATS score
    ↓
Recruiter review
    ↓
Human decision
```

This distinction is important for a serious recruitment product.
