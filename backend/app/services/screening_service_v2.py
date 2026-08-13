# Drop-in alternative for app/services/screening_service.py.
# It adds local MiniLM semantic similarity while preserving the deterministic score.
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
from app.services.embeddings import semantic_score
from app.services.bias_check import inspect_text

def screen_application_v2(db: Session, application_id: UUID, organization_id: UUID):
    started = time.perf_counter()
    application = db.scalar(select(Application).where(
        Application.id == application_id,
        Application.organization_id == organization_id,
    ))
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
    local_semantic = semantic_score(redacted, job.description)

    # Blend deterministic keyword score with local semantic similarity.
    semantic_blended = round(ats.semantic_score * 0.35 + local_semantic * 0.65, 2)
    overall = round(
        ats.keyword_score * 0.45
        + semantic_blended * 0.25
        + ats.experience_score * 0.20
        + ats.completeness_score * 0.10,
        2,
    )

    bias = inspect_text(redacted)
    ai, provider, model = explain(
        {
            "overall_score": overall,
            "strengths": ats.strengths,
            "concerns": ats.concerns + bias.flags,
        },
        job.description,
        redacted,
    )

    result = db.scalar(select(ScreeningResult).where(
        ScreeningResult.application_id == application.id
    ))
    if not result:
        result = ScreeningResult(
            organization_id=organization_id,
            application_id=application.id,
        )

    result.overall_score = overall
    result.keyword_score = ats.keyword_score
    result.semantic_score = semantic_blended
    result.experience_score = ats.experience_score
    result.completeness_score = ats.completeness_score
    result.recommendation = "STRONG_MATCH" if overall >= 80 and not ats.missing_required else "REVIEW" if overall >= 65 else "LOW_MATCH"
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
