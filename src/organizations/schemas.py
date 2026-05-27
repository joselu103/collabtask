# src/organizations/schemas.py
import uuid

from pydantic import BaseModel

from src.organizations.models import MemberRole


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class MemberInvite(BaseModel):
    user_id: uuid.UUID
    role: MemberRole = MemberRole.MEMBER
