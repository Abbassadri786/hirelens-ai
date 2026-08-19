"""Authentication primitives: JWT minting/verification, Argon2 password hashing,
cookie helpers.

Sets re-checked 'payload["type"]' by hand, and a caller that forgot would
happily accept a refresh token where an access token was required.

The access token's 'org' and 'role' claims are parsed into a typed object and
actually consumed by the request dependencies. They used to be written and
ignored, so a user switching organizations was silently pinned to
whichever membership row came first.

'constant_time_compare' backs CSRF validation, which previously used '=='.

'dummy_password_hash()' gives the login path a real hash to verify against
when the account does not exist, equalising response time so the endpoint
does not disclose which emails are registered.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Final, Literal
from uuid import UUID

import jwt
from fastapi import Response
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

ACCESS_COOKIE: Final = "hirelens_access"
REFRESH_COOKIE: Final = "hirelens_refresh"
CSRF_COOKIE: Final = "hirelens_csrf"

TokenType = Literal["access", "refresh"]

# Distinct audience per token type, so a refresh token cannot be replayed as
# an access token even if the 'type' claim were somehow tampered around.
AUDIENCE: Final[dict[str, str]] = {
    "access": "hirelens:access",
    "refresh": "hirelens:refresh",
}


class TokenError(ValueError):
    """Raised when a token is malformed, expired, or of the wrong type."""


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Validated claims from an access or refresh token."""

    user_id: UUID
    token_type: TokenType
    organization_id: UUID | None
    role: str | None
    jti: str

    @property
    def has_tenant(self) -> bool:
        return self.organization_id is not None


# ------------------------------------------------------------------
# Passwords
# ------------------------------------------------------------------


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except Exception:  # noqa: BLE001 - a malformed stored hash must not 500
        return False


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """A real Argon2 hash of a random secret, computed once.

    Verifying against this on the "user not found" branch of login makes that
    branch cost the same as a genuine failed verification, closing the timing
    side channel that revealed whether an email was registered.
    """
    return hash_password(secrets.token_urlsafe(32))


def constant_time_compare(left: str | None, right: str | None) -> bool:
    """Timing-safe string comparison that tolerates 'None'."""
    if left is None or right is None:
        return False
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


# ------------------------------------------------------------------
# Tokens
# ------------------------------------------------------------------


def _secret() -> str:
    return settings.JWT_SECRET_KEY.get_secret_value()


def create_token(
    *,
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    organization_id: UUID | None = None,
    role: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "aud": AUDIENCE[token_type],
        "iss": "hirelens",
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta,
        "jti": secrets.token_hex(16),
    }
    if organization_id is not None:
        payload["org"] = str(organization_id)
    if role is not None:
        payload["role"] = role

    return jwt.encode(payload, _secret(), algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    *, user_id: UUID, organization_id: UUID, role: str
) -> str:
    # noqa justification: 'token_type' is a discriminator literal, not a secret.
    return create_token(
        user_id=user_id,
        token_type="access",  # noqa: S106
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        organization_id=organization_id,
        role=role,
    )


def create_refresh_token(*, user_id: UUID) -> str:
    # noqa justification: 'token_type' is a discriminator literal, not a secret.
    return create_token(
        user_id=user_id,
        token_type="refresh",  # noqa: S106 discriminator literal, not a secret
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )


def decode_token(token: str, *, expected_type: TokenType) -> TokenClaims:
    """Decode and fully validate a token.

    Raises 'TokenError' for anything that is not a well-formed, unexpired token
    of exactly 'expected_type'.
    """
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[settings.JWT_ALGORITHM],
            audience=AUDIENCE[expected_type],
            issuer="hirelens",
            options={"require": ["exp", "iat", "sub", "type", "jti"]},
        )
    except InvalidTokenError as exc:
        raise TokenError(f"Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected {expected_type!r} token")

    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise TokenError("Token subject is not a valid identifier") from exc

    organization_id: UUID | None = None
    if raw_org := payload.get("org"):
        try:
            organization_id = UUID(str(raw_org))
        except ValueError as exc:
            raise TokenError("Token organization claim is malformed") from exc

    return TokenClaims(
        user_id=user_id,
        token_type=expected_type,
        organization_id=organization_id,
        role=payload.get("role"),
        jti=str(payload["jti"]),
    )


def hash_refresh_token(token: str) -> str:
    """Refresh tokens are stored only as hashes; never persist the raw value."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------
# Cookies
# ------------------------------------------------------------------


def _cookie_kwargs(*, http_only: bool) -> dict[str, Any]:
    return {
        "httponly": http_only,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "domain": settings.COOKIE_DOMAIN,
        "path": "/",
    }


def issue_csrf_cookie(response: Response) -> str:
    """Issue a fresh double-submit CSRF token.

    Deliberately not httpOnly: the browser client must read it to echo it back
    in the 'X-CSRF-Token' header. It carries no authority on its own.
    """
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        **_cookie_kwargs(http_only=False),
    )
    return csrf_token


def issue_auth_cookies(
    response: Response, *, access_token: str, refresh_token: str
) -> str:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **_cookie_kwargs(http_only=True),
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        **_cookie_kwargs(http_only=True),
    )
    return issue_csrf_cookie(response)


def clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            name,
            domain=settings.COOKIE_DOMAIN,
            path="/",
        )