import time
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.application import Application
from app.models.job import Job
from app.models.screening import ScreeningResult
from app.services.ats_engine import calculate_ats
from app.services.ai_explainer import explain
from app.services.pii_redaction import redact_pii, extract_sections

def screen_application(db: Session, application_id: UUID, organization_id: UUID):
    started = time.perf_counter()
    application = db.scalar(select(Application).where(Application.id == application_id, Application.organization_id == organization_id))
    if not application:
        raise ValueError("Application not found")
    job = db.scalar(select(Job).where(Job.id == application.job_id))
    if not job:
        raise ValueError("Job not found")

    redacted = redact_pii(application.resume.extracted_text or "")
    sections = extract_sections(redacted)
    required = [r.skill for r in job.requirements if r.is_required]
    preferred = [r.skill for r in job.requirements if not r.is_required]

    ats = calculate_ats(redacted, required, preferred, job.min_experience_years, len(sections))
    ai, provider, model = explain(
        {"overall_score": ats.overall_score, "strengths": ats.strengths, "concerns": ats.concerns},
        job.description, redacted
    )

    result = db.scalar(select(ScreeningResult).where(ScreeningResult.application_id == application.id))
    if not result:
        result = ScreeningResult(organization_id=organization_id, application_id=application.id)

    result.overall_score = ats.overall_score
    result.keyword_score = ats.keyword_score
    result.semantic_score = ats.semantic_score
    result.experience_score = ats.experience_score
    result.completeness_score = ats.completeness_score
    result.recommendation = ats.recommendation
    result.provider = provider
    result.model_name = model
    result.matched_skills = ats.matched_required
    result.missing_required_skills = ats.missing_required
    result.matched_preferred_skills = ats.matched_preferred
    result.strengths = ai["strengths"]
    result.concerns = ai["concerns"]
    result.improvement_suggestions = ai["improvement_suggestions"]
    result.explanation = ai["explanation"]
    result.resume_sections = sections
    result.redacted_text = redacted
    result.processing_ms = int((time.perf_counter() - started) * 1000)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
