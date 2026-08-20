"""Screening service - the single entry point for scoring an application.

This replaces two files, 'screening_service.py' and 'screening_service_v2.py'
were near-identical copies that had already diverged: v1 blended in local
fairness heuristics that didn't run under v2, did neither, and v2 recomputed the
recommendation with its own inlined copy of the threshold logic. Nothing
imported v2, so every feature added to it was dead code until now. Everything
further apart with each edit.

Responsibilities are now split cleanly:

* 'app.agents' owns the "decision" -- pure functions over a typed state, with no
  database access, so each stage is independently testable.
* This module owns the workflow and I/O -- loading inputs, writing the result, and
  recording the audit trail, all inside one transaction.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.agents.graph import PipelineError, run_pipeline
from app.agents.state import ScreeningState
from app.core.config import settings
from app.models.application import Application
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.services.audit_service import record_screening_decision

logger = logging.getLogger(__name__)


class ApplicationNotFound(ValueError):
    """The application does not exist within the caller's organization."""


class JobNotFound(ValueError):
    """The application references a job that no longer exists."""


def screen_application(
    db: Session,
    *,
    application_id: UUID,
    organization_id: UUID,
    actor_user_id: UUID | None = None,
) -> ScreeningResult:
    """Score one application, persist the result, and audit the decision.

    Raises 'ApplicationNotFound' / 'JobNotFound' for missing inputs and
    'PipelineError' when scoring itself fails.
    """
    application = _load_application(db, application_id, organization_id)
    job = _load_job(db, application.job_id, organization_id)

    state = _build_state(application, job)
    state = run_pipeline(state)

    result = _persist(db, state, application)
    record_screening_decision(
        db,
        organization_id=organization_id,
        application_id=application_id,
        actor_user_id=actor_user_id,
        payload=state.audit_payload(),
        bias_review_required=bool(state.bias and state.bias.review_required),
    )

    db.commit()
    db.refresh(result)
    return result


# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------


def _load_application(
    db: Session, application_id: UUID, organization_id: UUID
) -> Application:
    """Load the application with its resume and candidate in one round trip.

    The tenant predicate is part of the query rather than a check afterwards, so
    there is no code path that reads a row belonging to another organization.
    """
    application = db.scalar(
        select(Application)
        .options(
            joinedload(Application.resume),
            joinedload(Application.candidate),
        )
        .where(
            Application.id == application_id,
            Application.organization_id == organization_id,
        )
    )
    if application is None:
        raise ApplicationNotFound("Application not found")
    return application


def _load_job(db: Session, job_id: UUID, organization_id: UUID) -> Job:
    job = db.scalar(
        select(Job)
        .options(joinedload(Job.requirements))
        .where(Job.id == job_id, Job.organization_id == organization_id)
    )
    if job is None:
        raise JobNotFound("Job not found")
    return job


def _build_state(application: Application, job: Job) -> ScreeningState:
    """Assemble pipeline inputs from the loaded rows.

    The candidate's stored name is passed in so redaction can match it exactly
    rather than trying to infer names from the document.
    """
    candidate_names: tuple[str, ...] = ()
    if application.candidate is not None and application.candidate.full_name:
        candidate_names = (application.candidate.full_name,)

    return ScreeningState(
        application_id=application.id,
        organization_id=application.organization_id,
        job_id=job.id,
        candidate_id=application.candidate_id,
        raw_resume_text=(application.resume.extracted_text or "")
        if application.resume is not None
        else "",
        job_description=job.description or "",
        job_title=job.title or "",
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        min_experience_years=job.min_experience_years,
        known_names=candidate_names,
    )


# ------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------


def _persist(
    db: Session, state: ScreeningState, application: Application
) -> ScreeningResult:
    """Upsert the screening result for this application.

    One result per application is enforced by a unique constraint, so a re-run
    updates the existing row rather than accumulating history. The audit trail is
    what preserves the sequence of decisions.
    """
    if state.ats is None: # pragma: no cover - guaranteed by run_pipeline
        raise PipelineError("Cannot persist a result without a score")

    ats = state.ats
    result = db.scalar(
        select(ScreeningResult)
        .where(ScreeningResult.application_id == application.id)
    )
    if result is None:
        result = ScreeningResult(
            organization_id=state.organization_id,
            application_id=application.id,
        )
        db.add(result)

    result.overall_score = ats.overall_score
    result.keyword_score = ats.keyword_score
    result.semantic_score = ats.semantic_score
    result.experience_score = ats.experience_score
    result.completeness_score = ats.completeness_score
    result.recommendation = ats.recommendation

    result.provider = state.provider
    result.model_name = state.model_name
    result.semantic_backend = state.semantic_backend
    result.pipeline_version = state.pipeline_version

    result.matched_skills = ats.matched_required
    result.missing_required_skills = ats.missing_required
    result.matched_preferred_skills = ats.matched_preferred
    result.strengths = state.strengths
    result.concerns = state.concerns
    result.improvement_suggestions = state.improvement_suggestions
    result.explanation = state.explanation
    result.resume_sections = state.sections

    result.bias_flags = list(state.bias.flags) if state.bias else []
    result.bias_review_required = (
        state.bias.review_required if state.bias else False
    )

    # Retaining the redacted resume aids explainability but keeps candidate data
    # beyond the decision itself, so it is opt-out via configuration.
    result.redacted_text = state.llm_text if settings.STORE_REDACTED_TEXT else None
    result.processing_ms = state.total_duration_ms

    db.add(result)
    db.flush()
    return result