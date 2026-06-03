# src/users/service.py
import uuid

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import RefreshRequest, UserCreate
from src.users.security import hash_password, verify_password
from src.users.tokens import (
    JWTValidationException,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# Exceptions
class RegisterError(Exception): ...


class LoginError(Exception): ...


class RefreshError(Exception): ...


# Services
class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_new_user(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: information to create the new user.

        Returns:
            New user model.

        Raises:
            RegisterError: Unable to register user in the database.
        """
        try:
            new_user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hash_password(user_data.password),
            )
            await self.user_repo.create(new_user)
            return new_user
        except IntegrityError as e:
            raise RegisterError(f"Unable to create new user: {e}")

    async def login(self, user_data: OAuth2PasswordRequestForm) -> tuple[str, str]:
        """Verify the user data and creates an access token.

        Args:
            user_data: information to log in.

        Returns:
            Access and refresh tokens

        Raises:
            LoginError: Wrong email or password.
        """
        user = await self.user_repo.get_by_email(user_data.username)

        if not user:
            raise LoginError("User not found")

        if not verify_password(user_data.password, user.hashed_password):
            raise LoginError("Wrong password")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        return (access_token, refresh_token)

    async def refresh(self, refresh_data: RefreshRequest) -> tuple[str, str]:
        """Verify the refresh token and return it and a new access token.

        Args:
            refresh_data: contains the 'refresh_token'.

        Returns:
            New access token and same refresh token.

        Raises:
            RefreshToken: Invalid refresh token.
        """
        try:
            payload = decode_token(refresh_data.refresh_token)
        except JWTValidationException:
            raise RefreshError("Unable to decode token.")

        if payload.get("type") != "refresh":
            raise RefreshError("Invalid token type")

        try:
            user_id = uuid.UUID(payload["sub"])
        except ValueError:
            raise RefreshError(f"Invalid user id: {payload['sub']}")

        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise RefreshError("User not found")

        access_token = create_access_token(str(user.id))
        return (access_token, refresh_data.refresh_token)
