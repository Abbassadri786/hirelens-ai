from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from app.api.deps import DbSession, Membership, require_roles
from app.models.audit_event import AuditEvent
from app.models.user import UserRole

router = APIRouter(prefix="/audit", tags=["Audit"])
ROLES = (UserRole.ORGANIZATION_ADMIN,)

@router.get("", dependencies=[Depends(require_roles(*ROLES))])
def list_audit_events(
    db: DbSession,
    membership: Membership,
    limit: int = Query(50, ge=1, le=200),
):
    rows = db.scalars(
        select(AuditEvent)
        .where(AuditEvent.organization_id == membership.organization_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "entity_type": row.entity_type,
            "entity_id": (
                str(row.entity_id)
                if row.entity_id
                else None
            ),
            "actor_user_id": (
                str(row.actor_user_id)
                if row.actor_user_id
                else None
            ),
            "metadata": row.event_metadata,
            "created_at": row.created_at,
        }
        for row in rows
    ]
