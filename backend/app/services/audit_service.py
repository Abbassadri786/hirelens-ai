from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def record_event(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    entity_id: UUID | None = None,
    organization_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    request_id: str | None = None,
    metadata: dict | None = None,
):
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        event_metadata=metadata or {},
    )

    db.add(event)
    db.flush()

    return event