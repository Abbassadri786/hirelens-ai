# Apply Phase 2

This ZIP is an overlay for the Phase 1 project you already have running.

1. Extract this ZIP into the root of your Phase 1 repository.
2. Allow files to overwrite existing files.
3. Replace the Phase 1 `csrf()` function in `backend/app/api/v1/auth.py` with the function in `backend/app/api/v1/csrf_patch.py`.
4. Run:

```bash
docker compose down
docker compose up --build
```

5. Open `/dashboard/jobs`.
6. Create a job.
7. Click **Publish**.
8. Open `/jobs`.
9. Open the published role and submit a synthetic PDF/DOCX resume.
10. Use Swagger → `GET /api/v1/applications` to verify the application.

Phase 2 intentionally keeps uploaded files on local development storage. Do not expose
`backend/storage/resumes` as a public static directory. Phase 3 will introduce the AI
screening pipeline and production-oriented storage/worker boundaries.
