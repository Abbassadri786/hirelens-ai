"""Application endpoints, including the public apply form."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, StaffUser, require_csrf, require_staff
from app.core.rate_limit import upload_rate_limit
from app.models.application import Application, ApplicationStatus
from app.models.audit_event import AuditEventType
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.resume import Resume, ResumeStatus
from app.schemas.applications import (
    ApplicationResponse,
    ApplicationStatusUpdate,
    CandidateResponse,
    PublicApplicationForm,
    ResumeResponse,
)
from app.services.audit_service import record_event
from app.services.file_storage import delete_stored_resume, save_resume
from app.services.resume_parser import ResumeParseError, extract_resume_text
from app.services.tenant import get_org_application

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


def _to_response(application: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        candidate_id=application.candidate_id,
        resume_id=application.resume_id,
        status=application.status.value,
        submitted_at=application.submitted_at,
        candidate=CandidateResponse.model_validate(application.candidate),
        resume=ResumeResponse.model_validate(application.resume),
    )


def _load_with_relations(db: DbSession, application_id: UUID) -> Application | None:
    return db.scalar(
        select(Application)
        .options(
            joinedload(Application.candidate),
            joinedload(Application.resume),
        )
        .where(Application.id == application_id)
    )


@router.post(
    "/public/{job_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf), Depends(upload_rate_limit)],
)
async def apply(
    job_id: UUID,
    db: DbSession,
    full_name: str = Form(..., min_length=2, max_length=120),
    email: str = Form(..., alias="email", max_length=255),
    phone: str | None = Form(None, max_length=30),
    location: str | None = Form(None, max_length=120),
    cover_letter: str | None = Form(None, max_length=5_000),
    resume_file: UploadFile = File(...),
) -> ApplicationResponse:
    """Submit an application to a published, public job.

    Multipart form fields are validated through `PublicApplicationForm` so the
    same rules apply here as to any JSON endpoint.
    """
    form = PublicApplicationForm(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        cover_letter=cover_letter,
    )

    job = db.scalar(
        select(Job).where(
            Job.id == job_id,
            Job.status == JobStatus.PUBLISHED,
            Job.is_public.is_(True),
        )
    )
    if job is None:
        # A tame response whether the job is missing, unpublished or private, so
        # this cannot be used to probe for draft requisitions.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Published job not found"
        )

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.organization_id == job.organization_id,
            Candidate.email == form.email,
        )
    )
    if candidate is None:
        candidate = Candidate(
            organization_id=job.organization_id,
            full_name=form.full_name,
            email=form.email,
            phone=form.phone,
            location=form.location,
        )
        db.add(candidate)
        db.flush()

    existing = db.scalar(
        select(Application.id).where(
            Application.job_id == job.id,
            Application.candidate_id == candidate.id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate has already applied to this job",
        )

    stored = await save_resume(resume_file)
    try:
        extracted = extract_resume_text(stored.path, stored.file_type)
    except ResumeParseError as exc:
        # Do not leave an unreferenced file behind when the row is never created.
        delete_stored_resume(stored.path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except Exception as exc:
        delete_stored_resume(stored.path)
        logger.exception("Unexpected failure while parsing an uploaded resume")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume could not be processed",
        ) from exc

    resume = Resume(
        organization_id=job.organization_id,
        candidate_id=candidate.id,
        file_path=stored.path,
        file_type=stored.file_type,
        file_size_bytes=stored.file_size,
        status=ResumeStatus.PARSED,
        extracted_text=extracted,
        # Stored so admin/recruiter views can display the original filename.
        # Cleaned on model.
    )
    db.add(resume)
    db.flush()

    application = Application(
        organization_id=job.organization_id,
        job_id=job.id,
        candidate_id=candidate.id,
        resume_id=resume.id,
        cover_letter=form.cover_letter,
    )
    db.add(application)
    db.flush()

    record_event(
        db,
        event_type=AuditEventType.APPLICATION_SUBMITTED,
        entity_type="application",
        entity_id=application.id,
        organization_id=job.organization_id,
        metadata={"job_id": str(job.id), "resume_bytes": stored.file_size},
    )

    db.commit()

    created = _load_with_relations(db, application.id)
    if created is None: # pragma: no cover - just committed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application could not be loaded after creation",
        )
    return _to_response(created)


@router.get(
    "",
    response_model=list[ApplicationResponse],
    dependencies=[Depends(require_staff)],
)
def list_applications(
    db: DbSession,
    user: StaffUser,
    limit: int = 50,
    offset: int = 0,
) -> list[ApplicationResponse]:
    """List applications for the active tenant, newest first."""
    bounded_limit = max(1, min(limit, 200))

    items = (
        db.scalars(
            select(Application)
            .options(
                joinedload(Application.candidate),
                joinedload(Application.resume),
            )
            .where(Application.organization_id == user.organization_id)
            .order_by(Application.submitted_at.desc())
            .limit(bounded_limit)
            .offset(max(0, offset))
        )
        .unique()
        .all()
    )
    return [_to_response(item) for item in items]


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_staff)],
)
def get_application(
    application_id: UUID, db: DbSession, user: StaffUser
) -> ApplicationResponse:
    item = db.scalar(
        select(Application)
        .options(
            joinedload(Application.candidate),
            joinedload(Application.resume),
        )
        .where(
            Application.id == application_id,
            Application.organization_id == user.organization_id,
        )
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    return _to_response(item)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_csrf), Depends(require_staff)],
)
def update_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: DbSession,
    user: StaffUser,
) -> ApplicationResponse:
    """Move an application to a new status.

    Audited with both the previous and new value: rejecting a candidate is
    exactly the kind of decision that has to be reconstructable later.
    """
    item = get_org_application(db, application_id, user.organization_id)

    previous = item.status.value
    item.status = ApplicationStatus(payload.status)

    record_event(
        db,
        event_type=AuditEventType.APPLICATION_STATUS_CHANGED,
        entity_type="application",
        entity_id=item.id,
        organization_id=user.organization_id,
        actor_user_id=user.id,
        metadata={"from": previous, "to": item.status.value},
    )

    db.commit()

    updated = _load_with_relations(db, item.id)
    if updated is None: # pragma: no cover - just committed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application could not be reloaded",
        )
    return _to_response(updated)