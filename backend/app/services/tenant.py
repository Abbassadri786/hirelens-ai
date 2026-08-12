from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.job import Job


def get_org_job(db: Session, job_id: UUID, organization_id: UUID) -> Job:
    obj = db.scalar(
        select(Job).where(
            Job.id == job_id, Job.organization_id == organization_id
        )
    )
    if not obj:
        raise HTTPException(404, 'Job not found')
    return obj


def get_org_application(
    db: Session, application_id: UUID, organization_id: UUID
) -> Application:
    obj = db.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.organization_id == organization_id,
        )
    )
    if not obj:
        raise HTTPException(404, 'Application not found')
    return obj