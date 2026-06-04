# tests/integration/conftest.py
from dataclasses import dataclass

import pytest

from src.organizations.models import Organization, OrganizationMember
from src.projects.models import Project
from src.users.models import User
from src.users.tokens import create_access_token
from tests.factories import OrganizationFactory, UserFactory


@dataclass
class TestSetup:
    organization: Organization
    project: Project
    user: User
    access_token: str


@pytest.fixture
async def test_setup(db_session) -> TestSetup:
    organization = OrganizationFactory.build()
    user = UserFactory.build()

    db_session.add(organization)
    db_session.add(user)
    await db_session.flush()

    member = OrganizationMember(user_id=user.id, organization_id=organization.id)
    project = Project(name="test project", organization_id=organization.id)
    db_session.add(member)
    db_session.add(project)
    await db_session.commit()

    access_token = create_access_token(str(user.id))

    return TestSetup(
        organization=organization, user=user, project=project, access_token=access_token
    )
