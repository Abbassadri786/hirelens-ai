from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128

# A short deny-list of the shapes that dominate breach corpora. Not a
# substitute for a full breached-password check, but it costs nothing and stops
# the most common choices.
WEAK_PASSWORDS: frozenset[str] = frozenset(
    {
        "password",
        "password1",
        "password12",
        "password123",
        "password1234",
        "qwertyuiop",
        "123456789012",
        "letmein12345",
        "administrator",
        "changeme123",
        "welcome12345",
        "hirelens1234",
        "hirelens1234*",
    }
)


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(
        min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )
    organization_name: str = Field(min_length=2, max_length=160)

    @field_validator("password")
    @classmethod
    def password_is_strong(cls, value: str) -> str:
        """Require variety and reject well-known weak passwords."""
        if value.casefold() in WEAK_PASSWORDS:
            raise ValueError("This password is too common. Choose another.")

        # A single repeated character satisfies any length rule, so check it.
        if len(set(value)) < 5:
            raise ValueError("Password must contain at least 5 distinct characters")

        categories = sum(
            (
                any(ch.islower() for ch in value),
                any(ch.isupper() for ch in value),
                any(ch.isdigit() for ch in value),
                any(not ch.isalnum() for ch in value),
            )
        )
        if categories < 3:
            raise ValueError(
                "Password must combine at least three of: lowercase, "
                "uppercase, digits, symbols"
            )

        return value

    @field_validator("full_name", "organization_name")
    @classmethod
    def no_control_characters(cls, value: str) -> str:
        cleaned = value.replace("\x00", "").strip()
        if not cleaned:
            raise ValueError("Value cannot be blank")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    # No minimum here on purpose. Rejecting a short password at the schema layer
    # would answer "is this even a valid password shape" before authentication,
    # and returns a 422 where every failed login should look identical.
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str