# tests/integration/test_task_lifecycle.py
from dataclasses import dataclass

import faker
import pytest
import structlog

from src.organizations.models import Organization, OrganizationMember
from src.projects.models import Project
from src.tasks.schemas import TaskCreate, TaskResponse
from src.users.models import User
from src.users.tokens import create_access_token
from tests.factories import OrganizationFactory, UserFactory

logger = structlog.get_logger()


@dataclass
class TasksInput:
    organization: Organization
    project: Project
    user: User
    access_token: str


@pytest.fixture
async def test_setup(db_session) -> TasksInput:
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

    return TasksInput(
        organization=organization, user=user, project=project, access_token=access_token
    )


async def test_create_task(client, test_setup):
    # Given
    fake = faker.Faker()
    user, organization, project, access_token = (
        test_setup.user,
        test_setup.organization,
        test_setup.project,
        test_setup.access_token,
    )
    task_data = TaskCreate(title=fake.catch_phrase())

    # When
    response = await client.post(
        url=f"http://test/api/v1/organizations/{organization.id}/projects/{project.id}/tasks",
        headers={"Authorization": f"Bearer {access_token}"},
        json=task_data.model_dump(),
    )

    # Then
    assert response.status_code == 201
    TaskResponse.model_validate(response.json())
    assert response.json()["title"] == task_data.title
