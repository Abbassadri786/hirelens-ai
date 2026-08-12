import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, Membership, require_csrf, require_roles
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.resume import Resume, ResumeStatus
from app.models.user import UserRole
from app.schemas.applications import (
    ApplicationResponse,
    ApplicationStatusUpdate,
    CandidateResponse,
    ResumeResponse,
)
from app.services.file_storage import save_resume
from app.services.resume_parser import extract_resume_text
from app.services.tenant import get_org_application

router = APIRouter(prefix='/applications', tags=['Applications'])

ROLES = (
    UserRole.ORGANIZATION_ADMIN,
    UserRole.RECRUITER,
    UserRole.HIRING_MANAGER,
)


def clean(v, limit):
    return v.replace('\x00', '').strip()[:limit] if v else None


def email(v):
    v = v.strip().lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', v):
        raise HTTPException(422, 'Invalid candidate email')
    return v


def out(a):
    return ApplicationResponse(
        id=a.id,
        job_id=a.job_id,
        candidate_id=a.candidate_id,
        resume_id=a.resume_id,
        status=a.status.value,
        submitted_at=a.submitted_at,
        candidate=CandidateResponse.model_validate(a.candidate),
        resume=ResumeResponse.model_validate(a.resume),
    )


@router.post(
    '/public/jobs/{job_id}',
    response_model=ApplicationResponse,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
async def apply(
    job_id: UUID,
    db: DbSession,
    full_name: str = Form(..., min_length=2, max_length=160),
    email_value: str = Form(..., alias='email', max_length=320),
    phone: str | None = Form(None, max_length=40),
    location: str | None = Form(None, max_length=180),
    cover_letter: str | None = Form(None, max_length=10000),
    resume_file: UploadFile = File(...),
):
    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.status == JobStatus.PUBLISHED,
            Job.is_public.is_(True),
        )
    )
    if not job:
        raise HTTPException(404, 'Published job not found')

    candidate_email = email(email_value)
    candidate = db.scalar(
        select(Candidate).where(
            Candidate.organization_id == job.organization_id,
            Candidate.email == candidate_email,
        )
    )
    if not candidate:
        candidate = Candidate(
            organization_id=job.organization_id,
            full_name=clean(full_name, 160) or 'Candidate',
            email=candidate_email,
            phone=clean(phone, 40),
            location=clean(location, 180),
        )
        db.add(candidate)
        db.flush()

    existing = db.scalar(
        select(Application).where(
            Application.job_id == job.id,
            Application.candidate_id == candidate.id,
        )
    )
    if existing:
        raise HTTPException(409, 'Candidate has already applied to this job')

    upload = await save_resume(resume_file)
    try:
        extracted = extract_resume_text(upload['path'], upload['file_type'])
    except Exception as exc:
        Path(upload['path']).unlink(missing_ok=True)
        raise HTTPException(422, 'Resume parsing failed') from exc

    if not extracted.strip():
        Path(upload['path']).unlink(missing_ok=True)
        raise HTTPException(422, 'No readable text found in resume')

    resume = Resume(
        organization_id=job.organization_id,
        candidate_id=candidate.id,
        original_filename=upload['original_filename'],
        stored_filename=upload['stored_filename'],
        file_type=upload['file_type'],
        mime_type=upload['mime_type'],
        file_size=upload['file_size'],
        sha256=upload['sha256'],
        status=ResumeStatus.PARSED,
        extracted_text=extracted[:100000],
    )
    db.add(resume)
    db.flush()

    application = Application(
        organization_id=job.organization_id,
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        cover_letter=clean(cover_letter, 10000),
    )
    db.add(application)
    db.commit()

    result = db.scalar(
        select(Application)
        .options(
            joinedload(Application.candidate),
            joinedload(Application.resume),
        )
        .where(Application.id == application.id)
    )
    return out(result)


@router.get(
    '',
    response_model=list[ApplicationResponse],
    dependencies=[Depends(require_roles(*ROLES))],
)
def list_applications(db: DbSession, membership: Membership):
    items = (
        db.scalars(
            select(Application)
            .options(
                joinedload(Application.candidate),
                joinedload(Application.resume),
            )
            .where(Application.organization_id == membership.organization_id)
            .order_by(Application.submitted_at.desc())
        )
        .unique()
        .all()
    )
    return [out(x) for x in items]


@router.get(
    '/{application_id}',
    response_model=ApplicationResponse,
    dependencies=[Depends(require_roles(*ROLES))],
)
def get_application(
    application_id: UUID, db: DbSession, membership: Membership
):
    item = db.scalar(
        select(Application)
        .options(
            joinedload(Application.candidate),
            joinedload(Application.resume),
        )
        .where(
            Application.id == application_id,
            Application.organization_id == membership.organization_id,
        )
    )
    if not item:
        raise HTTPException(404, 'Application not found')
    return out(item)


@router.patch(
    '/{application_id}/status',
    response_model=ApplicationResponse,
    dependencies=[Depends(require_csrf), Depends(require_roles(*ROLES))],
)
def update_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: DbSession,
    membership: Membership,
):
    item = get_org_application(db, application_id, membership.organization_id)
    item.status = ApplicationStatus(payload.status)
    db.commit()

    item = db.scalar(
        select(Application)
        .options(
            joinedload(Application.candidate),
            joinedload(Application.resume),
        )
        .where(Application.id == item.id)
    )
    return out(item)