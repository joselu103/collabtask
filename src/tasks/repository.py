# src/tasks/repository.py

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.repository import BaseRepository
from src.tasks.models import Task


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    async def get_by_project(
        self, proj_id: uuid.UUID, limit: int, offset: int
    ) -> list[Task]:
        stmt = (
            select(Task).where(Task.project_id == proj_id).limit(limit).offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_project(self, proj_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Task).where(Task.project_id == proj_id)
        return await self.session.scalar(stmt)
