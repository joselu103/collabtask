# src/organizations/schemas.py
import uuid

from pydantic import BaseModel, ConfigDict

from src.organizations.models import MemberRole


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class MemberInvite(BaseModel):
    user_id: uuid.UUID
    role: MemberRole = MemberRole.MEMBER


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: MemberRole

    model_config = ConfigDict(from_attributes=True)
