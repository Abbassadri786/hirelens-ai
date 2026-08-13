from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

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
    provider: str
    model_name: str
    matched_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    improvement_suggestions: list[str]
    explanation: str
    resume_sections: dict
    processing_ms: int | None
    created_at: datetime

class ScreeningListItem(BaseModel):
    application_id: UUID
    candidate_name: str
    job_title: str
    submitted_at: datetime
    overall_score: float | None
    recommendation: str | None
    application_status: str
