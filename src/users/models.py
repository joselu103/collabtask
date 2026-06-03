# src/users/models.py
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models import BaseModel

if TYPE_CHECKING:
    from src.organizations.models import Organization


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    memberships: Mapped[list["Organization"]] = relationship(
        "Organization", secondary="organization_members", back_populates="members"
    )
