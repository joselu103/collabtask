# src/organizations/repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.organizations.models import Organization
from src.shared.repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organization)

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Return organization registered with the indicated slug"""
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
