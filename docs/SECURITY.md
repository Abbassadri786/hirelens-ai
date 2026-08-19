# Security and privacy design

The threat model, the controls that address it, and the limits of those controls.

---

## Threat model

The system ingests attacker-controlled files from an unauthenticated endpoint,
stores personal data about people who are not its users, and makes decisions that
affect their employment. That produces four concerns:

| Concern | Why it matters here |
|---|---|
| **Untrusted file parsing** | `POST /applications/public/{slug}/apply` accepts PDF/DOCX from anyone. Both are parsed by large native libraries with a long history of memory-safety CVEs. |
| **Candidate PII exposure** | Resumes contain names, contact details and sometimes protected attributes. Candidates never agreed to the operator's terms; sending that text to a third-party LLM whose terms permit training is an unannounced disclosure. |
| **Model provenance** | A score that moves silently when the underlying model drifts is indefensible. |
| **Decision accountability** | A screening score influences hiring, so it must be explainable, reproducible and auditable. |

---

## Secrets

No secret is present in source. All configuration is declared in
`app/core/config.py`, and:

- API keys are typed `SecretStr`, so they cannot surface through a log line, a
  traceback, or `repr(settings)`.
- `.env` is gitignored; only `.env.example` is committed.
- A production startup validator refuses to boot on unsafe configuration:
  - `DEBUG` must be `False`.
  - `COOKIE_SECURE` must be `True`.
  - `JWT_SECRET_KEY` cannot still be the `.env.example` placeholder.
  - `FRONTEND_ORIGIN` must use `https`.
- Rotate the JWT secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
  Rotating invalidates every existing session, which is intended.

---

## Authentication and sessions

- Passwords hashed with `PasswordHash.recommended()` (Argon2).
- Registration requires 12 characters, at distinct characters, and 3 of 4
  character classes, and rejects a deny-list of breach-corpus passwords. Length
  alone is insufficient -- "aaaaaaaaaaaa" satisfies a naive 12-character rule.
- Tokens are `**HttpOnly cookies**`, never `localStorage`, so XSS cannot read them.
- Access token lifetime 15 minutes, refresh token 7 days, stored only as SHA-256
  hashes so a database disclosure yields no usable session.
- `refresh()` rotates: **presenting a token revokes it and issues a new one**.
- `decode_token` validates the token `type` and a per-type `aud` claim, so a
  refresh token cannot be replayed as an access token.
- Login is **timing-equalized**: when the account does not exist the password is
  verified against a dummy Argon2 hash, so latency does not disclose which
  email addresses are registered.
- CSRF uses double-submit with a `**constant-time**` comparison.

### Limitation

Rotation detects reuse only in that a revoked token is rejected; it does not
track token `jti` families and will not retroactively invalidate a whole lineage
on replay.

---

## Authorization and tenancy

- A user belongs to exactly one organization and carries a role, so authorization
  is a direct check on the authenticated user:
  - `admin`
  - `recruiter`
- Every domain row carries an `organization_id`.
- Tenant predicates are part of the query (`.where(id == id, organization_id == id)`),
  not a check performed after loading -- there is no path that reads another
  tenant's row and then decides to reject it.
- A user whose membership table could be repaired for users spanning several
  organizations. That is deliberately not modelled -- nothing here needs it, and it
  would force every request to resolve a membership before it could authorize anything.

---

## File upload and parsing

Layered, in order, with nothing reaching a parser until every check passes:

1. **Extension allow-list** (`.pdf`, `.docx`).
2. **Declared MIME allow-list** -- client-supplied, so necessary but not sufficient.
3. **Magic-byte validator**, because `Content-Type` is trivially forged.
4. **Streaming size cap** enforced `while` reading, so an oversized upload is
   rejected before it is buffered.
5. **Decompression-bomb checks for DOCX**: A `.docx` is a ZIP archive, so a small
   upload can expand to gigabytes; the declared uncompressed size is read from
   the central directory and rejected above a 100x ratio, defusing nothing.
6. **Generated storage filenames** -- a UUID, never the client's, so path
   traversal and overwrite are impossible by construction.
7. **Page and element caps during extraction;** encrypted PDFs rejected.
8. The endpoint is rate-limited -- it is the only unauthenticated write.

### Limitation

Parsing runs **in-process**. A memory-safety exploit in MuPDF would execute with
the API process's privileges. The container mitigates blast radius by running as
a non-root user, but genuine isolation would mean a separate sandboxed process.

---

## PII handling and the model boundary

The **redaction node runs before every node that consumes text**, so "no
candidate PII reaches a third-party API" is enforced by pipeline ordering rather
than by each call site remembering.

Three views are produced, because they have different threat models:

| View | Contents | May leave the host? |
|---|---|---|
| `scoring_text` | Contact details removed; URLs intact (`"github.com/..."`); local scoring only | ✗ |
| `llm_text` | Names, addresses and URLs' paths also removed (`"github.com/"`); the only view that may | ✓ |
| `name_redacted_text` | `scoring_text` with only the candidate's name removed (`"Priya..."`); fairness counterfactual | ✗ |

- Names are matched against the candidate's `full_name`, so reduction does
  not depend on fragile NER. A heuristic header pass also catches maiden names,
  transliterations or nicknames.
- Header name lines (`HeaderLineCount = 4`) blanked.
- URLs are reduced to their `host/` (`"github.com/priya-redis/cache"` becomes
  `"github.com/"`): the platform signal that makes a resume assessable is
  preserved; the username that identifies the person is not.
- Audit metadata carries **counts, never values** -- recording what was redacted
  would recreate the exposure redaction exists to prevent.
- `extracted_text` is stored for explainability but never served by the API, and
  `redacted_text` is absent from every response schema.

### Free-tier providers train on your data

Free tiers of hosted LLM providers are commonly funded by retaining and training
on submitted data. **Trusting any text to Gemini or Groq on a free key as
personally disclosed.** This is why the architecture is shaped as it is:

- **Only `llm_text` is ever transmitted.**
- **Semantic matching runs *locally*** via `all-MiniLM-L6-v2` on CPU, in-process, so
  the most sensitive operation sends nothing anywhere. A privacy decision first,
  a cost decision second.
- **The chain terminates at Ollama** (local), the only provider marked
  `trusted_with_pii = True`, because nothing leaves the host. For real candidate data,
  production deployments should configure Ollama/local embeddings only.
- **Scores never depend on an LLM.** Models contribute narrative only, so disabling
  every provider degrades explanation quality and nothing else.

> **Do not point free-tier keys at production candidate data.** Use a paid tier
> with a no-training commitment, or run locally.

---

## Rate limiting

Applied as a dependency on the three endpoints that need it:

| Endpoint | Default | Purpose |
|---|---|---|
| `/auth/*` | 10/min | Password guessing |
| Public apply | 10/min | Attacker-supplied parsing and disk writes |
| Screening | 20/min | Protects the free-tier AI quota |

### Limitation

**Sliding-window in-memory.** Correct for a single container and sufficient to
protect a free-tier quota, but a multi-replica deployment needs a shared backend
(Redis) for the limit to be global.

---

## Fairness and explainability

Scoring is **fully deterministic**. That is a compliance property: a score is
reproducible and unit-testable in a way an LLM-assigned score is not.

Three checks run against every decision:

- **"Name sensitivity counterfactual"** -- the substantive one. The score is
  recomputed on a variant of the resume where *only* the candidate's name is removed.
  Because the scorer is a pure function, an identical score is returned; any delta is direct
  evidence that name-derived signal moved the outcome. Names are the documented
  proxy for gender and ethnicity in ATS discrimination litigation. Any delta
  escalates for human review.
- **"Protected attribute presence"** -- records which protected categories the
  source document mentions. Mere disclosure is not misconduct (resumes in many regions
  routinely include some), so it is recorded rather than escalated.
- **"Explanation hygiene"** -- flags a generated narrative that cites a protected
  attribute. An LLM told not to still do so, and the explanation is the
  artifact a candidate would receive.

Every decision writes an audit row with the sub-scores, their weighted
contributions, matched and missing skills, redaction counts, the fairness result,
and the provenance of each component (`provider`, `model_name`,
`semantic_backend`, `pipeline_version`). Fairness escalations get their own event
type so they are queryable without unpacking every row.

### Limitation

This detects **counterfactual name sensitivity**, which is zero by construction for a
deterministic scorer. It does **not** measure disparate impact across demographic
groups in aggregate -- that needs labeled demographic data the system
deliberately does not collect, but **adverse-impact testing** (e.g. the four-fifths
rule) is an offline analysis on a consented dataset.

---

## Transport and browser hardening

Set on every response: `X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, and `Cache-Control: no-store` on API routes so intermediaries
never store candidate data. HSTS is set in production only -- pinning it on
localhost would break the developer's browser profile.

CORS is restricted to a single configured origin with credentials enabled;
wildcard origins are rejected by the configuration parser.

---

## Findings this refactor closed

| Severity | Finding |
|---|---|
| **Critical** | `app/models/` did not exist. Two modules were imported by fifteen files; the application could not import, let alone run. |
| **Critical** | Names were never redacted -- resume text with the candidate's name intact was sent to a third-party LLM on a free tier. |
| **High** | Candidate inputs were accepted as free-form strings where leading whitespace, mixed casing, non-standard email shapes differed between tools. |
| **High** | The screening sync and async paths had diverged: the sync path used `v1` and the async path used `v2`. |
| **High** | The token check returned `True` for unauthenticated requests, bypassing all access control. |
| **High** | Semantic matching didn't check if the embedding library was installed, crashing rather than degrading to lexical. |
| **High** | The production frontend build failed: `useActionState` outside a Suspense boundary. |
| **High** | Open redirect on `frontend/src/start/page.tsx` accepts `//evil.example/`. |
| **Medium** | Password checking did not check for weak passwords or common dictionary words. |
| **Medium** | LLM failures were swallowed by a bare `except`, with no logging and `True` falsely configured even when missing keys. |
| **Medium** | The rate limiter mutated shared state from the thread pool without a lock. |
| **Medium** | AI keys bypassed 'settings.JWT_SECRET_KEY' and `None`, so `getenv` silently discarded five configured variables including both API keys. |
| **Low** | Time comparisons used `==`; login leaked account existence through timing. |
| **Low** | No DOCX decompression-ratio check (zip bomb), and the container ran as root while parsing untrusted files. |
| **Low** | `operations.py` duplicated check logic across five places, leaving three un-redacted. |
| **Low** | Open API doc broken: untyped or unversioned JSON layout of a config file that threw errors under Python 3. |