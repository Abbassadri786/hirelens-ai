# backend/app/api/v1/screening.py

"""Screening endpoints.

Screening runs synchronously. There was previously a durable job queue plus a
background worker, which is the right design once volume justifies it - but it
added a table, a service, a worker process and a container for work that
completes in well under a second here.

`screening_rate_limit` guards the endpoint that spends external AI quota.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.agents.graph import PipelineError
from app.api.deps import DbSession, StaffUser, require_csrf, require_staff
from app.core.rate_limit import screening_rate_limit
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.schemas.screening import ScreeningListItem, ScreeningResultResponse
from app.services.screening_service import (
    ApplicationNotFound,
    JobNotFound,
    screen_application,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/screening", tags=["AI Screening"])


@router.post(
    "/applications/{application_id}/run",
    response_model=ScreeningResultResponse,
    dependencies=[Depends(require_csrf), Depends(screening_rate_limit)],
)
def run_screening(
    application_id: UUID, db: DbSession, user: StaffUser
) -> ScreeningResult:
    """Score one application and persist the decision.

    The actor is recorded so the audit row captures *who* triggered the decision.
    """
    try:
        return screen_application(
            db,
            application_id,
            user.organization_id,
            actor_user_id=user.id,
        )
    except (ApplicationNotFound, JobNotFound) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PipelineError as exc:
        # Inputs were valid, so this is a server-side fault rather than a 4xx.
        logger.exception("Screening failed for %s: %s", application_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Screening could not be completed. Please retry.",
        ) from exc


@router.get(
    "/applications/{application_id}",
    response_model=ScreeningResultResponse,
    dependencies=[Depends(require_staff)],
)
def get_screening(
    application_id: UUID, db: DbSession, user: StaffUser
) -> ScreeningResult:
    """Fetch a stored screening result."""
    result = db.scalar(
        select(ScreeningResult).where(
            ScreeningResult.application_id == application_id,
            ScreeningResult.organization_id == user.organization_id,
        )
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Screening result not found"
        )
    return result


@router.get(
    "",
    response_model=list[ScreeningListItem],
    dependencies=[Depends(require_staff)],
)
def list_screenings(
    db: DbSession, user: StaffUser, limit: int = 100, offset: int = 0
) -> list[ScreeningListItem]:
    """List applications with their screening outcome, newest first."""
    bounded_limit = max(1, min(limit, 200))

    rows = db.execute(
        select(Application, Job, ScreeningResult)
        .join(Job, Job.id == Application.job_id)
        .outerjoin(
            ScreeningResult,
            ScreeningResult.application_id == Application.id,
        )
        .options(joinedload(Application.candidate))
        .where(Application.organization_id == user.organization_id)
        .order_by(Application.submitted_at.desc())
        .limit(bounded_limit)
        .offset(max(0, offset))
    ).all()

    return [
        ScreeningListItem(
            application_id=application.id,
            candidate_name=(
                application.candidate.full_name
                if application.candidate is not None
                else "Unknown candidate"
            ),
            job_id=job.id,
            job_title=job.title,
            submitted_at=application.submitted_at,
            overall_score=result.overall_score if result else None,
            recommendation=result.recommendation if result else None,
            application_status=application.status.value,
            bias_review_required=bool(result.bias_review_required) if result else False,
        )
        for application, job, result in rows
    ]