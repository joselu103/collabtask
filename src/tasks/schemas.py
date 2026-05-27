# src/tasks/schemas.py
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.tasks.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee_id: uuid.UUID | None = None
    priority: TaskPriority | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    project_id: uuid.UUID
    assignee_id: uuid.UUID | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskAssigneeUpdate(BaseModel):
    assignee_id: uuid.UUID


class TaskList(BaseModel):
    items: list[TaskResponse]
    total: int
