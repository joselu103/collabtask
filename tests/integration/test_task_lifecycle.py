# tests/integration/test_task_lifecycle.py
from unittest.mock import AsyncMock

import faker
import structlog

from src.organizations.models import OrganizationMember
from src.tasks.models import Task
from src.tasks.schemas import TaskAssigneeUpdate, TaskCreate, TaskResponse
from src.workers.dependencies import get_arq_pool
from tests.factories import UserFactory

logger = structlog.get_logger()


async def test_create_task(client, test_setup):
    # Given
    fake = faker.Faker()
    _, organization, project, access_token = (
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


async def test_assign_task(app, db_session, client, test_setup):
    # Given
    fake = faker.Faker()
    _, organization, project, access_token = (
        test_setup.user,
        test_setup.organization,
        test_setup.project,
        test_setup.access_token,
    )

    # Task
    task = Task(title=fake.catch_phrase(), project_id=project.id)
    db_session.add(task)

    # Other member
    asignee = UserFactory.build()
    member = OrganizationMember(user_id=asignee.id, organization_id=organization.id)
    db_session.add(asignee)
    await db_session.flush()

    db_session.add(member)
    await db_session.commit()

    request_data = TaskAssigneeUpdate(assignee_id=asignee.id)

    # Mock arq for email notification
    arq_mock = AsyncMock()
    app.dependency_overrides[get_arq_pool] = lambda: arq_mock

    # When
    response = await client.patch(
        url=f"http://test/api/v1/organizations/{organization.id}/projects/{project.id}/tasks/{task.id}/assign",
        headers={"Authorization": f"Bearer {access_token}"},
        json=request_data.model_dump(mode="json"),
    )

    # Then
    assert response.status_code == 200
    TaskResponse.model_validate(response.json())
    assert response.json()["assignee_id"] == str(asignee.id)
    arq_mock.enqueue_job.assert_called_once_with(
        "send_task_assigned_email", str(asignee.id), task.title
    )
