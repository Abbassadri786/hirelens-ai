from fastapi import APIRouter, Depends

from app.api.deps import Membership, require_roles
from app.models.user import UserRole
from app.schemas.auth import OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get(
    "/me",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_roles(
        UserRole.ORGANIZATION_ADMIN,
        UserRole.RECRUITER,
        UserRole.HIRING_MANAGER,
        UserRole.CANDIDATE,
    ))],
)
def get_my_organization(membership: Membership):
    return membership.organization
