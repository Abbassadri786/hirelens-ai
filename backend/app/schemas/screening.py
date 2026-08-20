from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScreeningResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID

    overall_score: float
    keyword_score: float
    semantic_score: float
    experience_score: float
    completeness_score: float
    recommendation: str

    # Pipeline metadata behind this result.
    provider: str
    model_name: str
    pipeline_version: str

    # Evidence behind the score.
    matched_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    improvement_suggestions: list[str]
    explanation: str
    resume_sections: dict[str, str]

    # Fairness.
    bias_flags: list[str] = Field(default_factory=list)
    bias_review_required: bool = False

    processing_ms: int | None
    created_at: datetime


class ScreeningListItem(BaseModel):
    """Row in the screening list view."""

    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    candidate_name: str
    job_id: UUID
    job_title: str
    submitted_at: datetime
    overall_score: float | None
    recommendation: str | None
    application_status: str
    bias_review_required: bool = False