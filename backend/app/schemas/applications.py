from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    phone: str | None
    location: str | None
    summary: str | None
    created_at: datetime


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    status: str
    created_at: datetime


class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID
    status: str
    submitted_at: datetime
    candidate: CandidateResponse
    resume: ResumeResponse


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(pattern='^(UNDER_REVIEW|SHORTLISTED|REJECTED)$')