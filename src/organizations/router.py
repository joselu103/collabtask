import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.organizations.repository import MemberRole
from src.organizations.schemas import (
    MemberInvite,
    MemberResponse,
    OrganizationCreate,
    OrganizationResponse,
)
from src.organizations.service import (
    CreateOrganizationError,
    InsufficientPermissionError,
    LastOwnerError,
    MemberNotFound,
    NewMemberError,
    OrganizationService,
    RemoveMemberError,
)
from src.shared.dependencies import get_active_user, require_organization_role
from src.users.models import User

router = APIRouter(prefix="/organizations")


def get_org_service(session: Annotated[AsyncSession, Depends(get_db)]):
    return OrganizationService(session=session)


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(get_active_user)],
    org_data: OrganizationCreate,
) -> OrganizationResponse:
    """Create a new organization. Its creator will be the first member
    and owner.

    Returns:
        The newly created organization data.

    Raises:
        HTTPException(400): Unable to create organization.
    """
    try:
        async with transaction(org_service.session):
            organization = await org_service.create_organization(
                requesting_user=user, data=org_data
            )
        return OrganizationResponse.model_validate(organization)
    except CreateOrganizationError, NewMemberError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Unable to create organization"
        )


@router.post("/{org_id}/members", response_model=MemberResponse)
async def invite_member(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(require_organization_role(MemberRole.ADMIN))],
    org_id: uuid.UUID,
    new_member_data: MemberInvite,
) -> MemberResponse:
    """Invite a member to the organization. The requesting user must be
    at least and admin of the organization.

    Returns:
        The new member data.

    Raises:
        HTTPException(403): User must be at least an admin of the organization.
        HTTPException(400): Unable to invite member.
    """
    try:
        async with transaction(org_service.session):
            new_member = await org_service.invite_member(
                org_id=org_id,
                data=new_member_data,
                requesting_user=user,
            )
        return MemberResponse.model_validate(new_member)
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be at least an admin of the organization.",
        )
    except NewMemberError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to invite new member")


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(require_organization_role(MemberRole.OWNER))],
    org_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Remove a member from the organization. The requesting user must be
    an owner of the organization.

    Raises:
        HTTPException(400): Unable to remove member.
        HTTPException(403): User is not an owner of the organization.
        HTTPException(404): Member not found.
        HTTPException(409): Can not remove the last owner of the organization.
    """
    try:
        async with transaction(org_service.session):
            await org_service.remove_member(
                org_id=org_id,
                user_id=user_id,
                requesting_user=user,
            )

    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "User is not an owner of the organization."
        )
    except MemberNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found.")
    except LastOwnerError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Can not remove the last owner of the organization.",
        )
    except RemoveMemberError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to remove member")
