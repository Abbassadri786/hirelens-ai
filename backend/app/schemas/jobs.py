from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.job import JobStatus

MAX_SKILLS = 50


def _clean_skill_list(value: list[str]) -> list[str]:
    """Strip, drop blanks, and de-duplicate case-insensitively.

    Normalizing at the schema boundary means the route no longer has to, and a
    payload of '["python", "Python", " "]' cannot create duplicate requirement
    rows that then double-count in the keyword score.
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in value:
        skill = raw.replace("\x00", "").strip()
        key = skill.casefold()
        if skill and key not in seen:
            seen.add(key)
            cleaned.append(skill[:120])
    return cleaned


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=20, max_length=10_000)
    location: str | None = Field(default=None, max_length=120)
    employment_type: str | None = Field(default=None, max_length=60)
    min_experience_years: int | None = Field(default=None, ge=0, le=50)
    required_skills: list[str] = Field(default_factory=list, max_length=MAX_SKILLS)
    preferred_skills: list[str] = Field(default_factory=list, max_length=MAX_SKILLS)

    @field_validator("title", "description")
    @classmethod
    def require_content(cls, value: str) -> str:
        cleaned = value.replace("\x00", "").strip()
        if not cleaned:
            raise ValueError("Value cannot be blank")
        return cleaned

    @field_validator("location", "employment_type", mode="before")
    @classmethod
    def clean_optional(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.replace("\x00", "").strip()
        return cleaned or None

    @field_validator("required_skills", "preferred_skills")
    @classmethod
    def _clean_skills(cls, value: list[str]) -> list[str]:
        return _clean_skill_list(value)


class JobUpdateRequest(BaseModel):
    """Partial update.

    The route applies this with 'exclude_unset=True', so omitting a field leaves
    it untouched while sending 'null' explicitly clears it.
    """

    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, min_length=20, max_length=10_000)
    location: str | None = Field(default=None, max_length=120)
    employment_type: str | None = Field(default=None, max_length=60)
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


class SkillDemand(BaseModel):
    """How often one skill appears across open requisitions."""

    skill: str
    count: int


class PublicJobAnalytics(BaseModel):
    """Aggregate public job-market view. Contains no candidate or tenant data."""

    total_jobs: int
    total_open_roles: int
    locations: int
    top_skills: list[SkillDemand] = Field(default_factory=list)