from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession, require_admin
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=list[AuditEventResponse],
    dependencies=[Depends(require_admin)],
)
def list_audit_events(
    db: DbSession,
    user: AdminUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    event_type: str | None = Query(default=None, max_length=40),
    entity_type: str | None = Query(default=None, max_length=40),
) -> list[AuditEvent]:
    """List audit events for the active tenant, newest first.

    The tenant predicate is mandatory, so an admin of one organization can never
    read another's trail. Rows with a NULL 'organization_id' -- failed logins
    before a tenant is known -- are deliberately excluded from tenant-scoped
    reads.
    """
    query = select(AuditEvent).where(
        AuditEvent.organization_id == user.organization_id
    )

    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if entity_type:
        query = query.where(AuditEvent.entity_type == entity_type)

    return list(
        db.scalars(
            query.order_by(AuditEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )