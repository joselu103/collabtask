# src/projects/models.py
import uuid

from sqlalchemy import UUID, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models import BaseModel


class Project(BaseModel):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("organizations.id"), nullable=False
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
