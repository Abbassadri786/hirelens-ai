from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.deps import DbSession, Membership, require_csrf, require_roles
from app.models.application import Application
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.models.user import UserRole
from app.schemas.screening import ScreeningResultResponse, ScreeningListItem
from app.services.screening_service import screen_application

router = APIRouter(prefix="/screening", tags=["AI Screening"])
ROLES = (UserRole.ORGANIZATION_ADMIN, UserRole.RECRUITER, UserRole.HIRING_MANAGER)

@router.post("/applications/{application_id}/run", response_model=ScreeningResultResponse, dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))])
def run_screening(application_id: UUID, db: DbSession, membership: Membership):
    try:
        return screen_application(db, application_id, membership.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get("/applications/{application_id}", response_model=ScreeningResultResponse, dependencies=[Depends(require_roles(*ROLES))])
def get_screening(application_id: UUID, db: DbSession, membership: Membership):
    result = db.scalar(select(ScreeningResult).where(
        ScreeningResult.application_id == application_id,
        ScreeningResult.organization_id == membership.organization_id
    ))
    if not result:
        raise HTTPException(status_code=404, detail="Screening result not found")
    return result

@router.get("", response_model=list[ScreeningListItem], dependencies=[Depends(require_roles(*ROLES))])
def list_screenings(db: DbSession, membership: Membership):
    rows = db.execute(
        select(Application, Job, ScreeningResult)
        .join(Job, Job.id == Application.job_id)
        .outerjoin(ScreeningResult, ScreeningResult.application_id == Application.id)
        .where(Application.organization_id == membership.organization_id)
        .order_by(Application.submitted_at.desc())
    ).all()
    return [
        ScreeningListItem(
            application_id=a.id,
            candidate_name=a.candidate.full_name,
            job_title=j.title,
            submitted_at=a.submitted_at,
            overall_score=r.overall_score if r else None,
            recommendation=r.recommendation if r else None,
            application_status=a.status.value,
        ) for a, j, r in rows
    ]
