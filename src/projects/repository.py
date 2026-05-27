# src/projects/repository.py

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.projects.models import Project
from src.shared.repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)

    async def get_by_organization(
        self, org_id: uuid.UUID, limit: int, offset: int
    ) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.organization_id == org_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_organization(self, org_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Project)
            .where(Project.organization_id == org_id)
        )
        return await self.session.scalar(stmt)
