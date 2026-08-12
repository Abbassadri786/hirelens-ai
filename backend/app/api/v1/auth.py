import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, require_csrf
from app.core.config import settings
from app.core.security import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    clear_auth_cookies,
    create_token,
    hash_password,
    hash_refresh_token,
    issue_auth_cookies,
    verify_password,
)
from app.models.organization import Organization, OrganizationMember
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    OrganizationResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def slugify(value: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return "-".join(part for part in base.split("-") if part)[:170] or "organization"


def build_tokens(user: User, membership: OrganizationMember) -> tuple[str, str, datetime]:
    access = create_token(
        user_id=user.id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
        organization_id=membership.organization_id,
        role=membership.role.value,
    )
    refresh = create_token(
        user_id=user.id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    return access, refresh, expires


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: DbSession):
    email = payload.email.lower().strip()

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")

    slug = slugify(payload.organization_name)
    if db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{slug}-{secrets.token_hex(3)}"

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
    )
    organization = Organization(name=payload.organization_name.strip(), slug=slug)
    db.add_all([user, organization])
    db.flush()

    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role=UserRole.ORGANIZATION_ADMIN,
    )
    db.add(membership)
    db.flush()

    access, refresh, expires = build_tokens(user, membership)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=expires,
        )
    )
    db.commit()

    issue_auth_cookies(response, access_token=access, refresh_token=refresh)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
    )


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: DbSession):
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    membership = db.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
        .order_by(OrganizationMember.created_at.asc())
        .limit(1)
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership")

    access, refresh, expires = build_tokens(user, membership)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=expires,
        )
    )
    db.commit()

    issue_auth_cookies(response, access_token=access, refresh_token=refresh)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
    )


@router.get("/csrf")
def csrf(response: Response):
    import secrets

    from app.core.security import CSRF_COOKIE

    token = secrets.token_urlsafe(32)
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path='/',
    )
    return {'message': 'CSRF token initialized'}


@router.post("/refresh", response_model=UserResponse, dependencies=[Depends(require_csrf)])
def refresh(
    response: Response,
    db: DbSession,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh session not found")

    try:
        from app.core.security import decode_token
        payload = decode_token(refresh_cookie)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh session")

    token_record = db.scalar(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == hash_refresh_token(refresh_cookie),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if not token_record or token_record.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh session expired")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")

    membership = db.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)
        .order_by(OrganizationMember.created_at.asc())
        .limit(1)
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership")

    # Rotate the refresh token so a stolen token cannot be replayed indefinitely.
    token_record.revoked_at = datetime.now(timezone.utc)
    access, new_refresh, expires = build_tokens(user, membership)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_refresh),
            expires_at=expires,
        )
    )
    db.commit()

    issue_auth_cookies(response, access_token=access, refresh_token=new_refresh)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
    )


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(
    response: Response,
    db: DbSession,
    current_user: CurrentUser,
):
    # Revoke every active refresh session for this user.
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now}, synchronize_session=False)
    db.commit()
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(
    current_user: CurrentUser,
    db: DbSession,
):
    membership = db.scalar(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
        .order_by(OrganizationMember.created_at.asc())
        .limit(1)
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization membership")

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=membership.role,
    )
