from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import ACCESS_COOKIE, CSRF_COOKIE, decode_token
from app.db.session import get_db
from app.models.organization import OrganizationMember
from app.models.user import User, UserRole

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    access_cookie: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
) -> User:
    if not access_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_token(access_cookie)
        if payload.get("type") != "access":
            raise ValueError("Wrong token type")
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication session",
        )

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_csrf(
    csrf_cookie: str | None = Cookie(default=None, alias=CSRF_COOKIE),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )


def get_membership(
    db: DbSession,
    user: CurrentUser,
) -> OrganizationMember:
    membership = db.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
        .order_by(OrganizationMember.created_at.asc())
        .limit(1)
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organization membership",
        )
    return membership


Membership = Annotated[OrganizationMember, Depends(get_membership)]


def require_roles(*roles: UserRole):
    def dependency(
        membership: Membership,
    ) -> OrganizationMember:
        if membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return membership

    return dependency
