"""FastAPI request dependencies: authentication, tenancy, authorization.

A user belongs to one organization and carries their role, so authorization is a
direct check against the authenticated user. There is no membership lookup:
`current_user.organization_id` is the tenant, and `current_user.role` is the
permission.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    TokenError,
    constant_time_compare,
    decode_token,
)
from app.db.session import get_db
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    access_cookie: Annotated[str | None, Cookie(alias=ACCESS_COOKIE)] = None,
) -> User:
    """Resolve the authenticated user from the access cookie."""
    if not access_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        claims = decode_token(access_cookie, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication session",
        ) from exc

    user = db.get(User, claims.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_csrf(
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE)] = None,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    """Double-submit CSRF check, compared in constant time."""
    if not constant_time_compare(csrf_cookie, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )


def require_roles(*roles: UserRole):
    """Build a dependency that authorizes the caller's role."""
    allowed = frozenset(roles)

    def dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            logger.warning(
                "Authorization denied for %s (role=%s)", user.id, user.role.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


# Roles permitted to work with recruitment data.
STAFF_ROLES: tuple[UserRole, ...] = (
    UserRole.ORGANIZATION_ADMIN,
    UserRole.RECRUITER,
    UserRole.HIRING_MANAGER,
)

require_staff = require_roles(*STAFF_ROLES)
require_admin = require_roles(UserRole.ORGANIZATION_ADMIN)

# Injects the authenticated staff user, having already authorized the role.
StaffUser = Annotated[User, Depends(require_staff)]
AdminUser = Annotated[User, Depends(require_admin)]