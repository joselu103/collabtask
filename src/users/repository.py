# src/users/respository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import BaseRepository
from src.users.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Return user registered with the indicated email"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
