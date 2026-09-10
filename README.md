# HireLens AI

### Explainable AI-Powered Recruitment Screening Workspace

HireLens AI is an enterprise-inspired Applicant Tracking and AI-assisted Resume Screening platform designed to help recruiters handle large candidate pools without manually reviewing every resume from scratch.

Instead of treating AI as a black-box hiring decision maker, HireLens combines deterministic ATS scoring, semantic matching, resume parsing, PII redaction, explainable AI feedback, asynchronous screening, audit logging, and recruiter review into one workflow.

> **AI assists the recruiter. It does not make the final hiring decision.**
<img width="1908" height="939" alt="Screenshot 2026-09-10 122749" src="https://github.com/user-attachments/assets/821d9c6c-5d2b-4e95-9110-58989604b76c" />
<img width="1908" height="944" alt="Screenshot 2026-09-10 122950" src="https://github.com/user-attachments/assets/47c7322b-c805-467d-a5f0-f4072ff29bf5" />
<img width="1919" height="945" alt="Screenshot 2026-09-10 123013" src="https://github.com/user-attachments/assets/954318b0-e5a1-4792-92bb-0bb2755daba8" />
<img width="1666" height="879" alt="Screenshot 2026-09-10 123037" src="https://github.com/user-attachments/assets/96acca0c-f2f0-4d8c-a8c7-bdd82a634c29" />
<img width="1668" height="882" alt="Screenshot 2026-09-10 123137" src="https://github.com/user-attachments/assets/e0ed5286-71d0-4082-9993-d1cd868dcf80" />
<img width="1910" height="944" alt="Screenshot 2026-09-10 123233" src="https://github.com/user-attachments/assets/2609310c-b28c-4c76-9da8-6c04f11581cd" />

---

## 🚀 Why HireLens AI?

Recruiters can receive hundreds or even thousands of applications for a single position.

Manually reviewing every resume creates several problems:

- ⏳ High screening time
- 📄 Repetitive resume review
- 🔍 Difficult comparison between candidates
- 🎯 Inconsistent screening criteria
- 🧩 Missing important skills hidden inside resumes
- 📊 Limited visibility into candidate pools
- 🤖 Difficulty using AI safely and explainably

HireLens AI addresses this by creating a structured screening pipeline:

```text
Job Requirement
       │
       ▼
Candidate Applies
       │
       ▼
Resume Upload
       │
       ▼
Secure File Validation
       │
       ▼
Resume Parsing
       │
       ▼
PII Redaction
       │
       ▼
ATS + Semantic Screening
       │
       ├───────────────┐
       │               │
       ▼               ▼
Keyword Match     Semantic Match
       │               │
       └───────┬───────┘
               ▼
        Explainable Score
               │
               ▼
      AI Feedback / Insights
               │
               ▼
       Recruiter Review
               │
               ▼
        Human Decision

---

# ✨ Core Features

## 🔐 Authentication & Authorization

* Secure signup and login
* HTTP-only authentication cookies
* Refresh-token based sessions
* Password hashing
* CSRF protection
* Role-based access control
* Recruiter / Hiring Manager / Organization Admin roles
* Protected frontend routes
* Automatic redirect when authentication expires
* Public and protected route separation
* Session-aware API client

---

## 💼 Recruitment Management

Recruiters can:

* Create recruitment roles
* Define job descriptions
* Specify required skills
* Specify preferred skills
* Define minimum experience
* Publish / close roles
* View applications
* Manage candidate pools
* Review candidate screening results

---

## 📄 Resume Management

HireLens supports:

* PDF resumes
* DOCX resumes
* File validation
* MIME-type validation
* File-size limits
* SHA-256 file hashing
* Secure storage metadata
* Resume parsing
* Extracted resume text
* Parsing status tracking

Supported resume lifecycle:

```text
UPLOADED
    │
    ▼
PARSED
    │
    └──► PARSE_FAILED
```

---

# 🧠 AI Screening Pipeline

HireLens does not simply send a resume and job description to an LLM and ask:

> "Is this candidate good?"

Instead, screening is composed of multiple stages.

```text
                    Resume
                       │
                       ▼
               ┌───────────────┐
               │ Resume Parser │
               └───────┬───────┘
                       │
                       ▼
                PII Redaction
                       │
                       ▼
             ┌───────────────────┐
             │ Screening Engine  │
             └─────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Keywords     Experience   Completeness
          │            │            │
          └────────────┼────────────┘
                       ▼
              Local Semantic Match
                       │
                       ▼
                ATS Score
                       │
                       ▼
              AI Explanation
                       │
                       ▼
              Recruiter Review
```

---

# 📊 Explainable ATS Scoring

The screening engine generates an overall score from multiple signals rather than relying entirely on an LLM.

Example:

```text
Overall Score       87 / 100

Keyword Match       91
Semantic Match      84
Experience Fit     100
Completeness        80
```

The system also identifies:

### Matched Skills

```text
✓ Python
✓ FastAPI
✓ PostgreSQL
✓ REST APIs
✓ Docker
```

### Missing Required Skills

```text
⚠ Kubernetes
⚠ AWS
```

### Strengths

```text
Strong backend development experience
Good alignment with required Python stack
Relevant API development experience
```

### Concerns

```text
Limited evidence of Kubernetes experience
AWS experience is not clearly demonstrated
```

### Improvement Suggestions

```text
Add quantified production achievements
Mention relevant cloud infrastructure work
Highlight deployment and DevOps experience
```

This makes the score **auditable and understandable** instead of presenting an unexplained AI number.

---

# 🤖 Generative AI

Gemini can be used for the explanation and feedback layer.

The architecture intentionally separates:

```text
Deterministic Screening
        +
Local Semantic Matching
        +
Generative AI Explanation
```

This prevents the LLM from becoming the sole source of truth for the ATS score.

---

# 🧩 Local Semantic Embeddings

HireLens uses:

```text
sentence-transformers
        +
all-MiniLM-L6-v2
```

for local semantic similarity.

Example:

```text
Resume:
"Built REST APIs using Python and FastAPI."

Job:
"Experience developing backend APIs with Python frameworks."

              ↓

Semantic similarity
              ↓

High match
```

This allows semantic matching without requiring a paid embedding API.

Benefits:

* 💰 Zero API cost
* 🔒 Resume content can remain local
* ⚡ Fast CPU inference for smaller workloads
* 🧠 Better than exact keyword matching alone

---

# 🛡️ Privacy & Security

Security is treated as a first-class architectural concern.

## Authentication

```text
Password
   ↓
Password Hash
   ↓
Database
```

Passwords are never stored as plaintext.

---

## Session Security

Authentication uses secure cookies rather than exposing tokens to normal JavaScript storage.

The frontend distinguishes:

```text
200 → authenticated

401 → authentication expired

403 → authenticated but forbidden

404 → resource/API not found

500 → server error

Network Error → backend unavailable
```

Only `401` triggers an authentication redirect.

This prevents the common:

```text
/auth/me → 404
      ↓
Login
      ↓
/auth/me → 404
      ↓
Login
      ↓
...
```

redirect loop.

---

## Resume Security

Uploaded resumes are validated using:

* File extension validation
* MIME validation
* File-size limits
* SHA-256 hashing
* Controlled storage filenames
* Server-side parsing

---

## PII Redaction

Before external AI processing, sensitive information can be removed or masked.

Examples:

```text
john@example.com
        ↓
[EMAIL_REDACTED]

+91 98765 43210
        ↓
[PHONE_REDACTED]
```

This reduces unnecessary exposure of candidate information.

---

# ⚖️ Responsible AI

HireLens is designed as a **decision-support system**, not an autonomous hiring system.

The platform does not intentionally use:

* Gender
* Religion
* Caste
* Ethnicity
* Race
* Age
* Health information
* Other protected attributes

as screening criteria.

The screening result should be treated as:

```text
AI-Assisted Screening Signal
            ↓
        Recruiter Review
            ↓
      Human Decision
```

not:

```text
AI Score < 60
      ↓
Automatic Rejection
```

This distinction is an important part of the system design.

---

# 🔍 Bias Detection

The screening pipeline includes a bias-checking layer that can flag potential protected-attribute references.

The goal is not to automatically decide whether a candidate should be rejected.

Instead, it helps identify potentially problematic signals and keeps the screening process explainable.

---

# ⚙️ Asynchronous Screening

A major design goal of HireLens is avoiding synchronous processing of large candidate pools.

Instead of:

```text
Recruiter Request
      ↓
Process 1000 resumes
      ↓
Wait 20 minutes
      ↓
Response
```

HireLens uses a queue:

```text
1000 Applications
       │
       ▼
Screening Queue
       │
       ├── QUEUED
       ├── RUNNING
       ├── COMPLETED
       └── FAILED
              │
              ▼
          Retry Logic
```

A dedicated worker processes screening jobs independently.

This makes the architecture more scalable and avoids blocking HTTP requests.

---

# 🧾 Audit Trail

Important screening operations are recorded.

Example:

```text
SCREENING_QUEUED
SCREENING_STARTED
SCREENING_COMPLETED
SCREENING_FAILED
```

Audit information can include:

* Event type
* Entity
* Actor
* Organization
* Timestamp
* Request ID
* Screening metadata

This provides traceability for recruiter actions and AI-assisted screening operations.

---

# 📈 Recruiter Analytics

The recruiter dashboard provides visibility into the candidate pipeline.

Example metrics:

```text
Open Roles
Applications
Screened Candidates
Average Screening Score
```

Candidate distribution:

```text
Strong Match
██████████████████

Needs Review
███████████

Low Match
██████
```

Recruiters can quickly understand:

* Candidate pool quality
* Screening progress
* Average candidate score
* Queue health
* Common screening outcomes

---

# 🎨 Product UI

HireLens is designed as a modern SaaS recruitment workspace rather than a collection of CRUD screens.

The UI includes:

* Responsive application shell
* Persistent recruiter navigation
* Mobile navigation drawer
* Breadcrumbs
* User menu
* Sign out
* Skeleton loaders
* Empty states
* Error states
* Retry actions
* Score visualization
* Candidate screening table
* Analytics dashboard
* Audit console
* Operations dashboard
* Responsive job cards

---

# 🏗️ Architecture

High-level architecture:

```text
┌──────────────────────────────────────────────┐
│                  Frontend                    │
│                                              │
│ Next.js + React + TypeScript + MUI          │
│                                              │
│ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│ │ Dashboard  │ │ Jobs       │ │ Screening│ │
│ └────────────┘ └────────────┘ └──────────┘ │
│                                              │
│ API Layer + Auth Context + Hooks             │
└──────────────────────┬───────────────────────┘
                       │
                       │ HTTP / Cookies
                       ▼
┌──────────────────────────────────────────────┐
│                  FastAPI                     │
│                                              │
│ Authentication                               │
│ Recruitment APIs                             │
│ Resume APIs                                  │
│ Screening APIs                               │
│ Analytics APIs                               │
│ Audit APIs                                   │
└──────────────────────┬───────────────────────┘
                       │
          ┌────────────┼───────────────┐
          │            │               │
          ▼            ▼               ▼
     PostgreSQL     AI Engine       File Storage
          │            │
          │       ┌────┴─────┐
          │       │          │
          │     Gemini    MiniLM
          │       │          │
          │       ▼          ▼
          │   Explanation  Semantic
          │                Matching
          │
          ▼
    Screening Queue
          │
          ▼
   Background Worker
```

---

# 🧰 Tech Stack

## Frontend

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| Next.js    | React application framework    |
| React      | UI development                 |
| TypeScript | Type-safe frontend development |
| MUI        | Component system and styling   |
| CSS        | Custom visual design           |
| Fetch API  | Backend communication          |

---

## Backend

| Technology | Purpose             |
| ---------- | ------------------- |
| Python     | Backend language    |
| FastAPI    | REST API framework  |
| SQLAlchemy | ORM                 |
| Alembic    | Database migrations |
| Pydantic   | Validation          |
| PostgreSQL | Primary database    |
| psycopg    | PostgreSQL driver   |

---

## AI / ML

| Technology            | Purpose                       |
| --------------------- | ----------------------------- |
| Google Gemini         | AI explanations and feedback  |
| Sentence Transformers | Local semantic embeddings     |
| all-MiniLM-L6-v2      | Resume/JD semantic similarity |
| Custom ATS Engine     | Deterministic scoring         |
| PII Redaction         | Privacy layer                 |

---

## Engineering

| Technology     | Purpose                        |
| -------------- | ------------------------------ |
| Docker         | Containerization               |
| Docker Compose | Local service orchestration    |
| Pytest         | Backend testing                |
| Git            | Version control                |
| REST API       | Frontend/backend communication |

---

# 📁 Project Structure

```text
hirelens-ai/
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── jobs.py
│   │   │       ├── resumes.py
│   │   │       ├── applications.py
│   │   │       ├── screening.py
│   │   │       ├── screening_bulk.py
│   │   │       ├── analytics.py
│   │   │       ├── operations.py
│   │   │       └── audit.py
│   │   │
│   │   ├── agents/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── nodes/
│   │   │   └── llm_router.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── rate_limit.py
│   │   │   └── logging_config.py
│   │   │
│   │   ├── db/
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── ats_engine.py
│   │   │   ├── embeddings.py
│   │   │   ├── pii_redaction.py
│   │   │   ├── bias_check.py
│   │   │   ├── screening_service.py
│   │   │   ├── screening_queue.py
│   │   │   └── audit_service.py
│   │   │
│   │   ├── workers/
│   │   │   └── screening_worker.py
│   │   │
│   │   └── main.py
│   │
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial.py
│   │       ├── 0002_recruitment_domain.py
│   │       ├── 0003_ai_screening.py
│   │       ├── 0004_screening_operations.py
│   │       └── 0005_screening_indexes.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── requirements.txt
│
├── frontend/
│   │
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── jobs.ts
│   │   │   ├── applications.ts
│   │   │   ├── screening.ts
│   │   │   ├── analytics.ts
│   │   │   ├── operations.ts
│   │   │   └── audit.ts
│   │   │
│   │   ├── app/
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   ├── jobs/
│   │   │   └── dashboard/
│   │   │
│   │   ├── components/
│   │   │   ├── analytics/
│   │   │   ├── auth/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── jobs/
│   │   │   ├── layout/
│   │   │   ├── navigation/
│   │   │   └── screening/
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   │
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── theme/
│   │   └── types/
│   │
│   └── package.json
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

# 🔄 Complete Product Flow

## Recruiter Flow

```text
Recruiter
   │
   ▼
Sign Up / Login
   │
   ▼
Recruiter Dashboard
   │
   ├───────────────┐
   │               │
   ▼               ▼
Create Job       Analytics
   │
   ▼
Define Requirements
   │
   ├── Required Skills
   ├── Preferred Skills
   ├── Experience
   └── Job Description
   │
   ▼
Publish Job
   │
   ▼
Candidate Applications
   │
   ▼
Screening Queue
   │
   ▼
AI Screening
   │
   ▼
Candidate Score
   │
   ▼
Explainable Evidence
   │
   ▼
Recruiter Review
   │
   ▼
Human Decision
```

---

# 👤 Candidate Flow

```text
Candidate
   │
   ▼
Public Job Board
   │
   ▼
Search / Browse Roles
   │
   ▼
View Job
   │
   ▼
Apply
   │
   ▼
Upload Resume
   │
   ▼
Secure Validation
   │
   ▼
Resume Parsing
   │
   ▼
Application Submitted
   │
   ▼
Screening Pipeline
```

---

# 🤖 AI Screening Flow

```text
Resume
  │
  ▼
Parser
  │
  ▼
Structured Resume
  │
  ▼
PII Redaction
  │
  ├──────────────────┐
  ▼                  ▼
ATS Engine      Local Embeddings
  │                  │
  │                  ▼
  │             Semantic Score
  │                  │
  └─────────┬────────┘
            ▼
       Weighted Score
            │
            ▼
     Gemini Explanation
            │
            ▼
     Screening Result
            │
            ▼
      Recruiter Review
```

---

# 📐 ATS Score Model

The score is intentionally explainable.

Conceptually:

```text
Overall Score
=
Keyword Match
+
Semantic Similarity
+
Experience Fit
+
Resume Completeness
```

Example weighting:

```text
Keyword Match       45%
Semantic Match      25%
Experience Fit      20%
Completeness        10%
```

The exact weighting can be adjusted as the screening model evolves.

---

# 🗃️ Database Model

Core entities:

```text
Organization
     │
     ├──────── Users
     │
     ├──────── Jobs
     │             │
     │             └── Job Requirements
     │
     ├──────── Candidates
     │             │
     │             └── Resumes
     │
     └──────── Applications
                    │
                    └── Screening Results
```

Operational entities:

```text
Screening Jobs
Audit Events
Refresh Tokens
```

---

# 🔒 Environment Variables

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

FRONTEND_ORIGIN=http://localhost:3000

SCREENING_WORKER_INTERVAL=2
```

Frontend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> Never commit `.env` files, API keys, database credentials, JWT secrets, refresh tokens, or real candidate resumes.

---

# 🛠️ Local Development

## 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/hirelens-ai.git

cd hirelens-ai
```

---

## 2. Backend

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure:

```text
.env
```

Run migrations:

```bash
alembic upgrade head
```

Start API:

```bash
uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# ⚙️ Start Screening Worker

Open another terminal:

```powershell
cd backend
.venv\Scripts\activate
python -m app.workers.screening_worker
```

The worker processes queued screening jobs.

---

# 🎨 Frontend

Open another terminal:

```bash
cd frontend
```

Install:

```bash
npm install
```

Start:

```bash
npm run dev
```

Application:

```text
http://localhost:3000
```

---

# 🧪 Testing

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run lint
```

Production build:

```bash
npm run build
```

---

# 🐳 Docker

API:

```bash
docker build -t hirelens-api ./backend
```

Worker:

```bash
docker build \
  -f backend/Dockerfile.worker \
  -t hirelens-worker \
  ./backend
```

For local multi-service development:

```bash
docker compose up --build
```

---

# 🚀 Deployment

Recommended architecture:

```text
                    Internet
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
     Next.js App               FastAPI API
      Vercel /                  Render /
      similar                   similar
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                    PostgreSQL            Screening Worker
                    Supabase              Separate service
```

Recommended production components:

```text
Frontend
→ Next.js

Backend
→ FastAPI

Database
→ PostgreSQL

AI
→ Gemini

Semantic Embeddings
→ Local Sentence Transformers

Worker
→ Python background worker

Containerization
→ Docker
```

---

# 📌 API Overview

Authentication:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
```

Jobs:

```text
GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/{job_id}
PATCH  /api/v1/jobs/{job_id}
DELETE /api/v1/jobs/{job_id}
```

Public jobs:

```text
GET    /api/v1/jobs/public
GET    /api/v1/jobs/public/{job_id}
GET    /api/v1/jobs/public/analytics
```

Applications:

```text
POST   /api/v1/applications
GET    /api/v1/applications
GET    /api/v1/applications/{application_id}
```

Screening:

```text
POST   /api/v1/screening/applications/{application_id}/enqueue
POST   /api/v1/screening/jobs/{job_id}/enqueue
GET    /api/v1/screening/{application_id}
```

Operations:

```text
GET    /api/v1/operations/screening-queue
```

Audit:

```text
GET    /api/v1/audit
```

---

# 🧠 Engineering Decisions

## Why FastAPI?

FastAPI provides:

* Strong typing
* Pydantic validation
* Automatic OpenAPI documentation
* Async support
* Excellent Python AI/ML ecosystem
* Simple service separation

---

## Why PostgreSQL?

The application contains strongly relational entities:

```text
Organizations
Users
Jobs
Requirements
Candidates
Resumes
Applications
Screening Results
Audit Events
```

PostgreSQL provides:

* Strong relational integrity
* Foreign keys
* Transactions
* JSONB
* Indexing
* Excellent scalability

---

## Why not MongoDB?

MongoDB could work for resume documents, but the core HireLens domain has strong relationships and transactional requirements.

PostgreSQL provides a better foundation for:

```text
Organization
    ↓
Job
    ↓
Application
    ↓
Candidate
    ↓
Resume
    ↓
Screening
```

---

## Why local embeddings?

Using a local embedding model reduces:

* API cost
* Vendor dependency
* PII exposure
* External network calls

while still enabling semantic matching.

---

## Why asynchronous screening?

A recruiter shouldn't have to keep an HTTP request open while processing hundreds of resumes.

The queue architecture provides:

```text
Fast API Response
        ↓
Background Processing
        ↓
Persistent Result
```

---

# 🧱 Design Principles

HireLens follows several engineering principles:

### Separation of concerns

```text
API
 ↓
Service
 ↓
Domain logic
 ↓
Database
```

### Type safety

TypeScript on the frontend and Pydantic on the backend.

### Explainability

Every screening result should have supporting evidence.

### Security by default

Authentication, authorization, validation, rate limiting, and secret management are part of the architecture.

### Human-in-the-loop

AI assists recruiters instead of replacing hiring decisions.

### Scalable processing

Long-running AI workloads are moved to background workers.

---

# 📊 Current Project Status

```text
Authentication              ████████████████████ 100%
Recruitment Management      ████████████████████ 100%
Resume Management           ████████████████████ 100%
ATS Scoring                 ████████████████████ 100%
Semantic Matching           ███████████████████░  90%
AI Explanation              ███████████████████░  90%
Async Screening             ███████████████████░  90%
Analytics                   █████████████████░░░  85%
Audit Logging               █████████████████░░░  85%
Production Hardening        ██████████████░░░░░░  70%
```

> Percentages represent project development maturity, not an external benchmark.

---

# 🗺️ Roadmap

## Completed

* [x] Authentication
* [x] Role-based authorization
* [x] Organization model
* [x] Job management
* [x] Candidate management
* [x] Resume upload
* [x] PDF/DOCX parsing
* [x] Application workflow
* [x] ATS scoring
* [x] Explainable screening
* [x] PII redaction
* [x] Local semantic embeddings
* [x] Screening queue
* [x] Background worker
* [x] Recruiter analytics
* [x] Audit logging
* [x] Protected frontend routes
* [x] Responsive recruiter workspace
* [x] Skeleton loading states
* [x] Error and empty states

## Planned

* [ ] Redis-backed distributed queue
* [ ] PostgreSQL pgvector integration
* [ ] Advanced candidate search
* [ ] Resume versioning
* [ ] Candidate comparison
* [ ] Bulk resume upload
* [ ] Advanced recruiter filters
* [ ] Saved searches
* [ ] Email notifications
* [ ] Interview scheduling
* [ ] Candidate pipeline / Kanban
* [ ] More comprehensive evaluation datasets
* [ ] AI evaluation benchmarks
* [ ] Automated bias evaluation experiments
* [ ] Production object storage
* [ ] Distributed worker scaling
* [ ] Observability with metrics/tracing
* [ ] CI/CD pipeline

---

# 🎯 What Makes This Project Different?

HireLens is intentionally more than:

```text
Upload Resume
      ↓
Call Gemini
      ↓
Show Score
```

The project demonstrates:

```text
                    Enterprise ATS
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
        ▼                ▼                 ▼
    Security         AI/ML Layer      Product Layer
        │                │                 │
        ▼                ▼                 ▼
    Auth/RBAC       ATS Engine        Recruiter UI
    CSRF            Embeddings        Analytics
    PII             Gemini            Audit
    Validation      Explainability    Queue
    Rate Limits     Bias Checks       Workers
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
                  Human-in-the-loop
```

This makes HireLens a strong demonstration of:

* Full-stack development
* Backend architecture
* AI integration
* NLP
* Semantic search
* Security
* Database design
* Asynchronous processing
* Product engineering
* Type-safe frontend architecture
* Responsible AI

---

# 💡 Interview Talking Points

HireLens can be used to demonstrate several real-world engineering discussions.

### Backend

* Why FastAPI?
* Why PostgreSQL?
* How would the architecture scale to 1M applications?
* How do you prevent duplicate screening?
* How does the queue handle failures?
* How would you implement distributed workers?

### AI

* Why not let Gemini generate the entire score?
* How does semantic similarity work?
* Why use local embeddings?
* How do you evaluate an AI screening system?
* How do you reduce hallucinations?
* How do you protect PII?

### Security

* Why HTTP-only cookies?
* How does CSRF protection work?
* How are passwords stored?
* How do you validate uploaded resumes?
* How do you prevent unauthorized cross-organization access?

### Frontend

* Why Next.js?
* Why TypeScript?
* How is server state separated from UI state?
* How does protected routing work?
* How are loading/error/empty states handled?
* How would you optimize a 10,000-row candidate table?

### System Design

* How would you process 100,000 applications?
* Why use background workers?
* Where would Redis fit?
* How would you scale AI inference?
* How would you implement observability?
* How would you design multi-tenant isolation?

---

# 🔬 Future Scaling Architecture

At larger scale, the architecture can evolve toward:

```text
                         Load Balancer
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
             Frontend                    API Cluster
                                             │
                         ┌───────────────────┼──────────────────┐
                         │                   │                  │
                         ▼                   ▼                  ▼
                     PostgreSQL          Redis Queue       Object Storage
                         │                   │                  │
                         │                   ▼                  │
                         │             Worker Cluster          │
                         │                   │                  │
                         │          ┌────────┴────────┐         │
                         │          │                 │         │
                         │          ▼                 ▼         │
                         │       ATS Engine       AI Service    │
                         │          │                 │         │
                         │          └────────┬────────┘         │
                         │                   │                  │
                         └───────────────────┼──────────────────┘
                                             ▼
                                      Screening Results
```

---

# 📄 License

This project is currently intended as a portfolio and educational project.

If you plan to use HireLens AI commercially, review and add an appropriate open-source or proprietary license before distribution.

---

# 👨‍💻 Author

**Abbas Sadriwala**

Full-Stack Developer focused on:

```text
Java
Spring Boot
Python
FastAPI
React
Next.js
TypeScript
PostgreSQL
AI / LLM Applications
```

---

## HireLens AI

### From Resume Screening → Explainable Candidate Intelligence

```text
Build smarter.
Screen faster.
Keep humans in control.
```

````

---

# A few GitHub-specific improvements I strongly recommend

Your README is only one part of making the repository look professional. I would also configure the repository like this:

### Repository root

```text
hirelens-ai/
├── README.md
├── LICENSE
├── .gitignore
├── docker-compose.yml
├── CONTRIBUTING.md
├── SECURITY.md
├── backend/
└── frontend/
````

### `SECURITY.md`

This is particularly valuable for your project because you're handling **resumes, PII, authentication, and AI**.

Use:

```markdown
# Security Policy

## Reporting a Vulnerability

Please do not publicly disclose security vulnerabilities.

Report vulnerabilities privately through the repository's security advisory mechanism.

## Sensitive Data

Never submit:

- passwords
- API keys
- JWT tokens
- refresh tokens
- real candidate resumes
- personally identifiable information

as GitHub issues, pull requests, fixtures, or demo data.

## AI Privacy

HireLens is designed to redact sensitive candidate information before optional external AI processing. Production deployments should review the privacy and data-retention policies of every external AI provider before processing real candidate data.
```
