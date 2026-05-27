# src/projects/schemas.py
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    organization_id: uuid.UUID
    is_archived: bool
    created_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectResponse]
    total: int
