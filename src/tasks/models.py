# src/tasks/models.py
import uuid
from enum import Enum

from sqlalchemy import UUID, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models import BaseModel


class TaskStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(BaseModel):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, default="", nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("projects.id"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus), default=TaskStatus.BACKLOG, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )
