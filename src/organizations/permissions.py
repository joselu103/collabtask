# src/organizations/permissions.py
import uuid

from src.organizations.models import MemberRole
from src.organizations.repository import OrganizationMemberRepository
from src.shared.exceptions import InsufficientPermissionError


async def check_role(
    member_repo: OrganizationMemberRepository,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    min_role: MemberRole,
) -> None:
    """Service level verification of a users role in an organization.

    Args:
        member_repo: instance of a OrganizationMemberRepository
        user_id: uuid of the user to verify
        organization_id: uuid of the organization to check
        min_role: minimum role necessary to pass the validation

    Raises:
        InsufficientPermissionError: if the user is not a member with
            a role high enough in the organization.
    """
    requesting_member = await member_repo.get_by_user_and_organization_ids(
        user_id=user_id, organization_id=organization_id
    )

    if not requesting_member or requesting_member.role < min_role:
        raise InsufficientPermissionError(
            f"User must be at least a {min_role} of the organization."
        )
