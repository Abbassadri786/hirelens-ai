from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=20, max_length=30000)
    location: str | None = Field(default=None, max_length=180)
    employment_type: str | None = Field(default=None, max_length=80)
    min_experience_years: int | None = Field(default=None, ge=0, le=50)
    required_skills: list[str] = Field(default_factory=list, max_length=50)
    preferred_skills: list[str] = Field(default_factory=list, max_length=50)


class JobUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(
        default=None, min_length=20, max_length=30000
    )
    location: str | None = Field(default=None, max_length=180)
    employment_type: str | None = Field(default=None, max_length=80)
    min_experience_years: int | None = Field(default=None, ge=0, le=50)
    status: JobStatus | None = None
    is_public: bool | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    location: str | None
    employment_type: str | None
    min_experience_years: int | None
    status: JobStatus
    is_public: bool
    created_at: datetime
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)