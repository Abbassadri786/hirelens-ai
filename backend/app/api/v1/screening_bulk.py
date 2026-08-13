from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.deps import DbSession, Membership, require_csrf, require_roles
from app.models.application import Application
from app.models.user import UserRole
from app.services.screening_queue import enqueue

router = APIRouter(prefix="/screening", tags=["AI Screening"])
ROLES = (UserRole.ORGANIZATION_ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)

@router.post("/jobs/{job_id}/enqueue", dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))])
def enqueue_job_applications(job_id: UUID, db: DbSession, membership: Membership):
    applications = db.scalars(select(Application).where(
        Application.organization_id == membership.organization_id,
        Application.job_id == job_id,
    )).all()
    if not applications:
        raise HTTPException(status_code=404, detail="No applications found for this job")

    jobs = [enqueue(db, a.id, membership.organization_id) for a in applications]
    return {"queued": len(jobs), "job_ids": [str(j.id) for j in jobs]}

@router.post("/applications/{application_id}/enqueue", dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))])
def enqueue_application(application_id: UUID, db: DbSession, membership: Membership):
    application = db.scalar(select(Application).where(
        Application.id == application_id,
        Application.organization_id == membership.organization_id,
    ))
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = enqueue(db, application.id, membership.organization_id)
    return {"id": str(job.id), "status": job.status}
