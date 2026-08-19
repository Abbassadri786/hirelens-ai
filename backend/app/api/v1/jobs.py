"""Job requisition endpoints.

Two things to note about route ordering and the new public analytics endpoint:

The endpoint aggregates only published, public requisitions and exposes no
candidate or tenant data.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, StaffUser, require_csrf, require_staff
from app.models.application import Application
from app.models.audit_event import AuditEventType
from app.models.job import Job, JobRequirement, JobStatus
from app.schemas.jobs import (
    JobCreateRequest,
    JobResponse,
    JobUpdateRequest,
    PublicJobAnalytics,
    SkillDemand,
)
from app.services.audit_service import record_event
from app.services.tenant import get_org_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# How many skills the public analytics view reports.
TOP_SKILL_LIMIT = 10


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        location=job.location,
        employment_type=job.employment_type,
        min_experience_years=job.min_experience_years,
        status=job.status,
        is_public=job.is_public,
        created_at=job.created_at,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
    )


def _published_public_filter():
    """Predicate for requisitions visible without authentication."""
    return (Job.status == JobStatus.PUBLISHED, Job.is_public.is_(True))


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf), Depends(require_staff)],
)
def create(
    payload: JobCreateRequest,
    db: DbSession,
    user: StaffUser,
) -> JobResponse:
    """Create a requisition with its required and preferred skills."""
    job = Job(
        organization_id=user.organization_id,
        created_by=user.id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        employment_type=payload.employment_type,
        min_experience_years=payload.min_experience_years,
    )
    db.add(job)
    db.flush()

    # De-duplication is case-insensitive and spans both lists, so a skill listed
    # as required and preferred is stored once, as required.
    seen: set[str] = set()
    for skill, is_required in (
        *((s, True) for s in payload.required_skills),
        *((s, False) for s in payload.preferred_skills),
    ):
        key = skill.casefold()
        if key in seen:
            continue
        seen.add(key)
        db.add(
            JobRequirement(
                job_id=job.id, skill=skill[:120], is_required=is_required
            )
        )

    record_event(
        db,
        event_type=AuditEventType.JOB_CREATED,
        entity_type="job",
        entity_id=job.id,
        organization_id=user.organization_id,
        actor_user_id=user.id,
        metadata={"required_skills": len(payload.required_skills)},
    )
    db.commit()
    db.refresh(job)
    return _to_response(job)


# -----------------------------------------------------------------------------
# Public routes
#
# Literal segments must precede '/{job_id}'; see the module docstring.
# -----------------------------------------------------------------------------


@router.get("/public", response_model=list[JobResponse])
def public_jobs(db: DbSession, limit: int = 50, offset: int = 0) -> list[JobResponse]:
    """List published public requisitions."""
    bounded_limit = max(1, min(limit, 100))
    jobs = (
        db.scalars(
            select(Job)
            .options(joinedload(Job.requirements))
            .where(*_published_public_filter())
            .order_by(Job.created_at.desc())
            .limit(bounded_limit)
            .offset(max(0, offset))
        )
        .unique()
        .all()
    )
    return [_to_response(job) for job in jobs]


@router.get("/public/analytics", response_model=PublicJobAnalytics)
def public_job_analytics(db: DbSession) -> PublicJobAnalytics:
    """Aggregate view of the public job market on this instance.

    Every figure is derived from published, public requisitions only, and no
    candidate or organization data is exposed. Aggregation runs in the database
    rather than by loading rows and counting in Python.
    """
    published = _published_public_filter()

    # Every requisition ever made public, including those since closed. This is
    # a genuinely different figure from the currently-open count below - the two
    # were previously computed from identical predicates and always matched.
    total_jobs = (
        db.scalar(select(func.count(Job.id)).where(Job.is_public.is_(True))) or 0
    )

    open_roles = db.scalar(select(func.count(Job.id)).where(*published)) or 0

    distinct_locations = (
        db.scalar(
            select(func.count(func.distinct(func.lower(Job.location)))).where(
                *published, Job.location.is_not(None)
            )
        )
        or 0
    )

    # Group by the case-folded skill so "Python" and "python" are one entry.
    skill_rows = db.execute(
        select(
            func.min(JobRequirement.skill).label("skill"),
            func.count(JobRequirement.job_id).label("demand"),
        )
        .join(Job, Job.id == JobRequirement.job_id)
        .where(*published)
        .group_by(func.lower(JobRequirement.skill))
        .order_by(func.count(JobRequirement.id).desc())
        .limit(TOP_SKILL_LIMIT)
    ).all()

    return PublicJobAnalytics(
        total_jobs=total_jobs,
        total_open_roles=open_roles,
        locations=distinct_locations,
        top_skills=[
            SkillDemand(skill=row.skill, count=row.demand) for row in skill_rows
        ],
    )


@router.get("/public/{job_id}", response_model=JobResponse)
def public_job(job_id: UUID, db: DbSession) -> JobResponse:
    """Fetch one published public requisition."""
    job = db.scalar(
        select(Job)
        .options(joinedload(Job.requirements))
        .where(Job.id == job_id, *_published_public_filter())
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Published job not found"
        )
    return _to_response(job)


# -----------------------------------------------------------------------------
# Authenticated routes
# -----------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[JobResponse],
    dependencies=[Depends(require_staff)],
)
def list_jobs(db: DbSession, user: StaffUser) -> list[JobResponse]:
    jobs = (
        db.scalars(
            select(Job)
            .options(joinedload(Job.requirements))
            .where(Job.organization_id == user.organization_id)
            .order_by(Job.created_at.desc())
        )
        .unique()
        .all()
    )
    return [_to_response(job) for job in jobs]


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_staff)],
)
def get_job(
    job_id: UUID, db: DbSession, user: StaffUser
) -> JobResponse:
    return _to_response(get_org_job(db, job_id, user.organization_id))


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_csrf), Depends(require_staff)],
)
def update(
    job_id: UUID,
    payload: JobUpdateRequest,
    db: DbSession,
    user: StaffUser,
) -> JobResponse:
    """Apply a partial update.

    `exclude_unset` distinguishes 'field omitted' from 'field explicitly set to
    None' -- an empty string wiped any 'None', so a field could never be
    cleared once populated.
    """
    job = get_org_job(db, job_id, user.organization_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(job, field, value.strip() if isinstance(value, str) else value)

    record_event(
        db,
        event_type=AuditEventType.JOB_UPDATED,
        entity_type="job",
        entity_id=job.id,
        organization_id=user.organization_id,
        actor_user_id=user.id,
        metadata={"fields": sorted(updates)},
    )
    db.commit()
    db.refresh(job)
    return _to_response(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf), Depends(require_staff)],
)
def delete(
    job_id: UUID,
    db: DbSession,
    user: StaffUser,
) -> None:
    """Delete a requisition that has no applications.

    Applications are refused rather than cascaded: deleting them would destroy
    screening decisions the audit trail references.
    """
    job = get_org_job(db, job_id, user.organization_id)

    application_count = (
        db.scalar(
            select(func.count(Application.id)).where(Application.job_id == job.id)
        )
        or 0
    )
    if application_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Jobs with applications cannot be deleted",
        )

    record_event(
        db,
        event_type=AuditEventType.JOB_DELETED,
        entity_type="job",
        entity_id=job.id,
        organization_id=user.organization_id,
        actor_user_id=user.id,
        metadata={"title": job.title},
    )
    db.delete(job)
    db.commit()