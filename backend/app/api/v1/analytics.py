from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from app.api.deps import DbSession, Membership, require_roles
from app.models.application import Application
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.models.user import UserRole

router = APIRouter(prefix="/analytics", tags=["Analytics"])
ROLES = (UserRole.ORGANIZATION_ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)

@router.get("/overview", dependencies=[Depends(require_roles(*ROLES))])
def overview(db: DbSession, membership: Membership):
    org = membership.organization_id
    jobs = db.scalar(select(func.count(Job.id)).where(Job.organization_id == org)) or 0
    apps = db.scalar(select(func.count(Application.id)).where(Application.organization_id == org)) or 0
    screened = db.scalar(select(func.count(ScreeningResult.id)).where(ScreeningResult.organization_id == org)) or 0
    avg = db.scalar(select(func.avg(ScreeningResult.overall_score)).where(ScreeningResult.organization_id == org)) or 0
    strong = db.scalar(select(func.count(ScreeningResult.id)).where(ScreeningResult.organization_id == org, ScreeningResult.recommendation == "STRONG_MATCH")) or 0
    review = db.scalar(select(func.count(ScreeningResult.id)).where(ScreeningResult.organization_id == org, ScreeningResult.recommendation == "REVIEW")) or 0
    low = db.scalar(select(func.count(ScreeningResult.id)).where(ScreeningResult.organization_id == org, ScreeningResult.recommendation == "LOW_MATCH")) or 0
    return {
        "total_jobs": jobs,
        "total_applications": apps,
        "screened_applications": screened,
        "average_score": round(float(avg), 2),
        "recommendations": {"strong_match": strong, "review": review, "low_match": low},
    }
