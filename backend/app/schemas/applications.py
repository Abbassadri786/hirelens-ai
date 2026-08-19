"""Application schemas.

Candidate inputs were previously accepted as free-form strings where subtle
differences (leading whitespace, mixed casing, non-standard email shapes) that
differed between tools would either cause a hard database error or silently
coerce a blank name into the literal string "Candidate", so validation rules
are consolidated here rather than everywhere else.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Statuses a recruiter can move an application through.
AVAILABLE_STATUSES = ("UNDER_REVIEW", "SHORTLISTED", "REJECTED")
# Statuses that can only be set system-side, or transition to CREATED and WITHDRAWN
# is the candidate's action, so neither is settable here.


def _strip_control_characters(value: str) -> str:
    """Remove NUL and surrounding whitespace.

    A NUL byte in a text column raises a driver-level error on PostgreSQL, so
    stripping it here turns a 500 into clean input.
    """
    return value.replace("\x00", "").strip()


class PublicApplicationForm(BaseModel):
    """Validated multipart fields from the public apply endpoint."""

    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=120)
    cover_letter: str | None = Field(default=None, max_length=10_000)

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_name(cls, value: object) -> object:
        return _strip_control_characters(value) if isinstance(value, str) else value

    @field_validator("phone", "location", "cover_letter", mode="before")
    @classmethod
    def clean_optionals(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = _strip_control_characters(value)
        return cleaned or None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


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
    """Resume metadata only.

    'extracted_text' is intentionally absent: the API has no reason to serve raw
    resume content back, and including it would widen PII exposure to every
    client that lists applications.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    file_type: str
    file_size_int: int
    status: str
    created_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID
    status: str
    submitted_at: datetime
    candidate: CandidateResponse
    resume: ResumeResponse


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(UNDER_REVIEW|SHORTLISTED|REJECTED)$")