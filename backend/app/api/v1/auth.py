from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, require_csrf
from app.core.config import settings
from app.core.rate_limit import auth_rate_limit
from app.core.security import (
    REFRESH_COOKIE,
    TokenError,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_password_hash,
    hash_password,
    hash_refresh_token,
    issue_auth_cookies,
    issue_csrf_cookie,
    verify_password,
)
from app.models.audit_event import AuditEventType
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.audit_service import record_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(auth_rate_limit)],
)

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
)


def slugify(value: str) -> str:
    """URL-safe organization slug."""
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return "-".join(part for part in base.split("-") if part)[:70] or "organization"


def _issue_session(db: Session, response: Response, user: User) -> None:
    """Mint an access/refresh pair, persist the refresh hash, set cookies."""
    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_DAYS),
        )
    )

    issue_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest, response: Response, db: DbSession
) -> UserResponse:
    """Create an organization and its first admin user."""
    email = payload.email.lower().strip()

    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )

    slug = slugify(payload.organization_name)
    if db.scalar(select(Organization.id).where(Organization.slug == slug)):
        slug = f"{slug}-{secrets.token_hex(3)}"

    organization = Organization(name=payload.organization_name.strip(), slug=slug)
    db.add(organization)
    db.flush()

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        organization_id=organization.id,
        role=UserRole.ORGANIZATION_ADMIN,
    )
    db.add(user)
    db.flush()

    _issue_session(db, response, user)
    record_event(
        db,
        event_type=AuditEventType.USER_REGISTERED,
        entity_type="user",
        entity_id=user.id,
        organization_id=organization.id,
        actor_user_id=user.id,
    )
    db.commit()

    logger.info("Registered organization %s", organization.slug)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest, response: Response, db: DbSession
) -> UserResponse:
    """Authenticate and start a session."""
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        # Verify against a throwaway hash so the "no such user" branch costs the
        # same as a real failed verification. Without this, response latency
        # discloses whether an address is registered.
        verify_password(payload.password, dummy_password_hash())
        record_event(
            db,
            event_type=AuditEventType.USER_LOGIN_FAILED,
            entity_type="user",
            metadata={"reason": "unknown_email"},
        )
        db.commit()
        raise INVALID_CREDENTIALS

    if not verify_password(payload.password, user.password_hash):
        record_event(
            db,
            event_type=AuditEventType.USER_LOGIN_FAILED,
            entity_type="user",
            entity_id=user.id,
            organization_id=user.organization_id,
            metadata={"reason": "bad_password"},
        )
        db.commit()
        raise INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled"
        )

    _issue_session(db, response, user)
    record_event(
        db,
        event_type=AuditEventType.USER_LOGGED_IN,
        entity_type="user",
        entity_id=user.id,
        organization_id=user.organization_id,
        actor_user_id=user.id,
    )
    db.commit()

    return UserResponse.model_validate(user)


@router.get("/csrf")
def csrf(response: Response) -> dict[str, str]:
    """Issue a CSRF token for a client with no session yet.

    Needed by the public application form, which posts without being logged in.
    """
    issue_csrf_cookie(response)
    return {"message": "CSRF token initialized"}


@router.post(
    "/refresh",
    response_model=UserResponse,
    dependencies=[Depends(require_csrf)],
)
def refresh(
    response: Response,
    db: DbSession,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
) -> UserResponse:
    """Rotate the refresh token and issue a new access token."""
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session not found",
        )

    try:
        claims = decode_token(refresh_cookie, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        ) from exc

    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_cookie),
            RefreshToken.revoked_at.is_(None),
        )
    )

    if token_record is None or token_record.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session expired",
        )

    if token_record.user_id != claims.user_id:
        # The signed subject and the stored row disagree; treat as tampering.
        logger.error("Refresh token subject mismatch for %s", token_record.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    user = db.get(User, claims.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    # Rotate: revoke the presented token so a stolen copy cannot be replayed.
    token_record.revoked_at = datetime.now(UTC)
    _issue_session(db, response, user)
    db.commit()

    return UserResponse.model_validate(user)


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(
    response: Response, db: DbSession, current_user: CurrentUser
) -> dict[str, str]:
    """Revoke every active refresh session for the caller."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(UTC)}, synchronize_session=False)
    db.commit()

    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    """Return the authenticated user."""
    return UserResponse.model_validate(current_user)