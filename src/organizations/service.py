# src/organizations/service.py
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.organizations.models import MemberRole, Organization, OrganizationMember
from src.organizations.repository import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from src.organizations.schemas import MemberInvite, OrganizationCreate
from src.users.models import User


class CreateOrganizationError(Exception): ...


class InviteMemberError(Exception): ...


class RemoveMemberError(Exception): ...


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.org_repo = OrganizationRepository(session)
        self.member_repo = OrganizationMemberRepository(session)

    async def create_organization(
        self, user: User, data: OrganizationCreate
    ) -> Organization:
        """Create a new Organization model with the user as owner.

        Args:
            user: the user creating the organization.
            data: necessary information about the new organization.

        Returns:
            New organization model.

        Raises:
            CreateOrganizationError: if the creation of the organization
                or the creation of the owner membership fails.
        """
        try:
            organization = Organization(**data.model_dump())
            await self.org_repo.create(organization)
        except Exception as e:
            raise CreateOrganizationError(f"Error while creating the organization: {e}")

        try:
            member = OrganizationMember(
                user_id=user.id, organization_id=organization.id, role=MemberRole.OWNER
            )
            await self.member_repo.create(member)
        except Exception as e:
            raise CreateOrganizationError(
                f"Error while adding the owner to the organization: {e}"
            )

        return organization

    async def invite_member(
        self, org_id: uuid.UUID, data: MemberInvite, requesting_user: User
    ) -> OrganizationMember:
        """Add a new member to an organization.

        Args:
            org_id: the UUID of the organization.
            data: necessary information about the new member.
            requesting_user: user requesting the operation.

        Returns:
            New organization member model.

        Raises:
            InviteMemberError: if the member addition fails.
        """
        requesting_member = await self.member_repo.get_by_user_and_organization_ids(
            user_id=requesting_user.id, organization_id=org_id
        )
        if not requesting_member or requesting_member.role < MemberRole.ADMIN:
            raise InviteMemberError(
                "Requesting user doesn't meet the requirements to invite other members."
            )
        try:
            member = OrganizationMember(organization_id=org_id, **data.model_dump())
            await self.member_repo.create(member)
        except Exception as e:
            raise InviteMemberError(
                f"Error while adding a new member to the organization: {e}"
            )
        return member

    async def remove_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID, requesting_user: User
    ) -> None:
        """Remove a user from an organization.

        Args:
            org_id: the UUID of the organization.
            user_id: the UUID of the user to remove.
            requesting_user: user requesting the operation.

        Raises:
            RemoveMemberError: if the member removal fails.
        """
        requesting_member = await self.member_repo.get_by_user_and_organization_ids(
            user_id=requesting_user.id, organization_id=org_id
        )
        if not requesting_member or requesting_member.role != MemberRole.OWNER:
            raise RemoveMemberError(
                "Requesting user doesn't meet the requirements to remove other members."
            )

        member_to_remove = await self.member_repo.get_by_user_and_organization_ids(
            user_id=user_id, organization_id=org_id
        )
        if not member_to_remove:
            raise RemoveMemberError("User is not a member of the organization.")

        if await self._is_removing_last_owner(requesting_user, user_id, org_id):
            raise RemoveMemberError(
                "Can not remove the last owner of the organization."
            )

        try:
            await self.member_repo.delete(member_to_remove)
        except Exception as e:
            raise RemoveMemberError(
                f"Error while removing member from the organization: {e}."
            )

    async def _is_removing_last_owner(
        self, requesting_user: User, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> bool:
        if requesting_user.id != user_id:
            return False

        owners = await self.member_repo.get_by_role_and_organization_id(
            role=MemberRole.OWNER, organization_id=org_id
        )

        return len(owners) <= 1

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
