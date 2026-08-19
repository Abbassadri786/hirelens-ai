from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent, AuditEventType

logger = logging.getLogger(__name__)


def record_event(
    db: Session,
    *,
    event_type: AuditEventType | str,
    entity_type: str,
    entity_id: UUID | None = None,
    organization_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append one audit row within the caller's transaction."""
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        event_metadata=metadata or {},
    )
    db.add(event)
    db.flush()
    return event


def record_screening_decision(
    db: Session,
    *,
    organization_id: UUID,
    application_id: UUID,
    actor_user_id: UUID | None,
    payload: dict[str, Any],
    bias_review_required: bool,
) -> None:
    """Record a completed screening decision, plus a fairness event if flagged."""
    record_event(
        db,
        event_type=AuditEventType.SCREENING_COMPLETED,
        entity_type="application",
        entity_id=application_id,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        metadata=payload,
    )

    if bias_review_required:
        # A separate event so fairness escalations are queryable without
        # unpacking every completion row's metadata.
        record_event(
            db,
            event_type=AuditEventType.SCREENING_BIAS_FLAGGED,
            entity_type="application",
            entity_id=application_id,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            metadata={"fairness": payload.get("fairness", {})},
        )
        logger.warning("Screening decision %s flagged for review", application_id)