"""Organization endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.models.organization import Organization
from app.schemas.auth import OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/me", response_model=OrganizationResponse)
def get_my_organization(current_user: CurrentUser) -> Organization:
    """Return the organization the caller belongs to.

    No role guard: being authenticated already establishes membership of exactly
    one organization, which is the whole authorization requirement here.
    """
    return current_user.organization