# src/organizations/models.py
import uuid
from enum import Enum as PyEnum

from sqlalchemy import UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models import BaseModel
from src.users.models import User


class MemberRole(str, PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    @property
    def order(self):
        return {MemberRole.MEMBER: 1, MemberRole.ADMIN: 2, MemberRole.OWNER: 3}[self]

    def __lt__(self, other):
        if not isinstance(other, MemberRole):
            return NotImplemented
        return self.order < other.order


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    members: Mapped[list["User"]] = relationship(
        "User", secondary="organization_members", back_populates="memberships"
    )


class OrganizationMember(BaseModel):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "organization_id", name="uq_organization_members_user_org"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("users.id"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("organizations.id"), nullable=False
    )
    role: Mapped[MemberRole] = mapped_column(
        SAEnum(MemberRole), default=MemberRole.MEMBER, nullable=False
    )
