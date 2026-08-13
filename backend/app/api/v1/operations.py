from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from app.api.deps import DbSession, Membership, require_roles
from app.models.screening_job import ScreeningJob
from app.models.user import UserRole

router = APIRouter(prefix="/operations", tags=["Operations"])
ROLES = (UserRole.ORGANIZATION_ADMIN, RECRUITER, HIRING_MANAGER) if False else (UserRole.ORGANIZATION_ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)

@router.get("/screening-queue", dependencies=[Depends(require_roles(*ROLES))])
def screening_queue_stats(db: DbSession, membership: Membership):
    rows = db.execute(
        select(ScreeningJob.status, func.count(ScreeningJob.id))
        .where(ScreeningJob.organization_id == membership.organization_id)
        .group_by(ScreeningJob.status)
    ).all()
    return {status: count for status, count in rows}
