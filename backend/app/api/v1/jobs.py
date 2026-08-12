from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import (
    CurrentUser,
    DbSession,
    Membership,
    require_csrf,
    require_roles,
)
from app.models.job import Job, JobRequirement, JobStatus
from app.models.user import UserRole
from app.schemas.jobs import JobCreateRequest, JobResponse, JobUpdateRequest
from app.services.tenant import get_org_job

router = APIRouter(prefix='/jobs', tags=['Jobs'])

ROLES = (
    UserRole.ORGANIZATION_ADMIN,
    UserRole.RECRUITER,
    UserRole.HIRING_MANAGER,
)


def out(job: Job) -> JobResponse:
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
        required_skills=[r.skill for r in job.requirements if r.is_required],
        preferred_skills=[
            r.skill for r in job.requirements if not r.is_required
        ],
    )


@router.post(
    '',
    response_model=JobResponse,
    status_code=201,
    dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))],
)
def create(
    payload: JobCreateRequest,
    db: DbSession,
    user: CurrentUser,
    membership: Membership,
):
    job = Job(
        organization_id=membership.organization_id,
        created_by=user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        location=payload.location.strip() if payload.location else None,
        employment_type=(
            payload.employment_type.strip() if payload.employment_type else None
        ),
        min_experience_years=payload.min_experience_years,
    )
    db.add(job)
    db.flush()
    seen = set()

    for skill, required in [
        (s, True) for s in payload.required_skills
    ] + [(s, False) for s in payload.preferred_skills]:
        value = skill.strip()
        key = value.casefold()
        if value and key not in seen:
            db.add(
                JobRequirement(
                    job_id=job.id, skill=value[:120], is_required=required
                )
            )
            seen.add(key)

    db.commit()
    db.refresh(job)
    return out(job)


@router.get('/public', response_model=list[JobResponse])
def public_jobs(db: DbSession):
    return [
        out(x)
        for x in db.scalars(
            select(Job)
            .where(Job.status == JobStatus.PUBLISHED, Job.is_public.is_(True))
            .order_by(Job.created_at.desc())
        ).all()
    ]


@router.get(
    '',
    response_model=list[JobResponse],
    dependencies=[Depends(require_roles(*ROLES))],
)
def list_jobs(db: DbSession, membership: Membership):
    return [
        out(x)
        for x in db.scalars(
            select(Job)
            .where(Job.organization_id == membership.organization_id)
            .order_by(Job.created_at.desc())
        ).all()
    ]


@router.get('/public/{job_id}', response_model=JobResponse)
def public_job(job_id: UUID, db: DbSession):
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.status == JobStatus.PUBLISHED,
            Job.is_public.is_(True),
        )
    )
    if not job:
        raise HTTPException(404, 'Published job not found')
    return out(job)


@router.get(
    '/{job_id}',
    response_model=JobResponse,
    dependencies=[Depends(require_roles(*ROLES))],
)
def get_job(job_id: UUID, db: DbSession, membership: Membership):
    return out(get_org_job(db, job_id, membership.organization_id))


@router.patch(
    '/{job_id}',
    response_model=JobResponse,
    dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))],
)
def update(
    job_id: UUID,
    payload: JobUpdateRequest,
    db: DbSession,
    membership: Membership,
):
    job = get_org_job(db, job_id, membership.organization_id)
    for field in (
        'title',
        'description',
        'location',
        'employment_type',
        'min_experience_years',
        'status',
        'is_public',
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(
                job,
                field,
                value.strip() if isinstance(value, str) else value,
            )
    db.commit()
    db.refresh(job)
    return out(job)


@router.delete(
    '/{job_id}',
    status_code=204,
    dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))],
)
def delete(job_id: UUID, db: DbSession, membership: Membership):
    job = get_org_job(db, job_id, membership.organization_id)
    if job.applications:
        raise HTTPException(409, 'Jobs with applications cannot be deleted')
    db.delete(job)
    db.commit()