import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.organizations.schemas import (
    MemberInvite,
    OrganizationCreate,
    OrganizationResponse,
)
from src.organizations.service import (
    CreateOrganizationError,
    InviteMemberError,
    OrganizationService,
    RemoveMemberError,
)
from src.shared.dependencies import get_active_user, get_db
from src.users.models import User

router = APIRouter(prefix="/organizations")


def get_org_service(session: Annotated[AsyncSession, Depends(get_db)]):
    return OrganizationService(session=session)


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(get_active_user)],
    org_data: OrganizationCreate,
):
    """Create a new organization. Its creator will be the first member
    and owner.
    """
    try:
        organization = await org_service.create_organization(user=user, data=org_data)
        await org_service.commit()
        return OrganizationResponse(**organization)
    except CreateOrganizationError:
        await org_service.rollback()
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Unable to create organization"
        )


@router.post("/{org_id}/members", response_model=MemberInvite)
async def invite_member(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(get_active_user)],
    org_id: uuid.UUID,
    new_member_data: MemberInvite,
):
    """Invite a member to the organization. The requesting user must be
    at least and admin of the organization.
    """
    try:
        await org_service.invite_member(
            org_id=org_id,
            data=new_member_data,
            requesting_user=user,
        )
        await org_service.commit()
        return new_member_data
    except InviteMemberError:
        await org_service.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to invite new member")


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_service: Annotated[OrganizationService, Depends(get_org_service)],
    user: Annotated[User, Depends(get_active_user)],
    org_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Remove a member from the organization. The requesting user must be
    an owner of the organization.
    """
    try:
        await org_service.remove_member(
            org_id=org_id,
            user_id=user_id,
            requesting_user=user,
        )
        await org_service.commit()
    except RemoveMemberError:
        await org_service.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to remove member")
