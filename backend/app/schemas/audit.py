"""Audit trail schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """One audit row.

    `metadata` is aliased from the model's `event_metadata` attribute, which
    exists because `metadata` is reserved on a SQLAlchemy declarative class. The
    API keeps the natural name.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    event_type: str
    entity_type: str
    entity_id: UUID | None
    actor_user_id: UUID | None
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="event_metadata"
    )
    created_at: datetime