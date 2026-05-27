# src/users/service.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import UserCreate
from src.users.security import hash_password


# Exceptions
class RegisterError(Exception): ...


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
