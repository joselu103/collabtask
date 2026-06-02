# src/shared/dependencies.py
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db
from src.organizations.models import MemberRole
from src.organizations.repository import OrganizationMemberRepository
from src.users.models import User
from src.users.repository import UserRepository
from src.users.tokens import JWTValidationException, decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Resolve the authenticated user from the Bearer token.

    Decodes and validates the JWT, then fetches the corresponding user
    from the database.

    Returns:
        The authenticated User instance.

    Raises:
        HTTPException(401): Token is missing, invalid, expired, or wrong
            type.
        HTTPException(404): No user found for the token's subject.
    """
    try:
        payload = decode_token(token)
    except JWTValidationException:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        sub = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository(session).get_by_id(sub)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    return user


async def get_active_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Extend get_current_user to require an active account.

    Raises:
        HTTPException(403): The authenticated user's account is inactive.
    """
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User is not active.")
    return user


def require_organization_role(required_role: MemberRole):
    """Creates a dependency that ensures that the current active user is
    a member of an organization with a high enough role.

    Args:
        required_role: Minimum role required.

    Returns:
        The authenticated User model with the required role.

    Raises:
        HTTPException(403): User is not a member of the organization
            or does not meet the required role.
    """

    async def check_role(
        user: Annotated[User, Depends(get_active_user)],
        org_id: Annotated[uuid.UUID, Path()],
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        """Verify the active user holds the required role in the target
        organization.
        """
        member = await OrganizationMemberRepository(
            session
        ).get_by_user_and_organization_ids(user.id, org_id)
        if not member:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "User is not a member of the organization."
            )
        if member.role < required_role:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "User doesn't meet the required role."
            )
        return user

    return check_role
