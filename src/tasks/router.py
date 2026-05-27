# src/tasks/router.py
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.organizations.repository import MemberRole
from src.projects.service import (
    ProjectNotFound,
)
from src.shared.dependencies import require_organization_role
from src.shared.exceptions import InsufficientPermissionError
from src.tasks.schemas import (
    TaskAssigneeUpdate,
    TaskCreate,
    TaskList,
    TaskResponse,
    TaskStatusUpdate,
)
from src.tasks.service import (
    CreateTaskError,
    InvalidAssignee,
    TaskNotFound,
    TaskService,
)
from src.tasks.state_machine import InvalidTransitionError
from src.users.models import User

# TODO Consider passing down org_id to services and skip project and skip
# validations

router = APIRouter(prefix="/{project_id}/tasks", tags=["tasks"])


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    return TaskService(session=session)


# GET /api/v1/organizations/{org_id}/projects/{project_id}/tasks
@router.get("", response_model=TaskList)
async def get_task_list(
    user: Annotated[User, Depends(require_organization_role(MemberRole.MEMBER))],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    limit: int,
    offset: int,
) -> TaskList:
    """Obtain a wrapped list with the tasks of a project and the total
    amount.

    Raises:
        HTTPException(403): User must be a member of the organization.
        HTTPException(404): Project not found.
    """
    try:
        items, total = await task_service.list_tasks(
            requesting_user=user, project_id=project_id, limit=limit, offset=offset
        )
        return TaskList(
            items=[TaskResponse.model_validate(p) for p in items], total=total
        )
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be a member of the organization.",
        )
    except ProjectNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")


# POST /api/v1/organizations/{org_id}/projects/{project_id}/tasks
@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    user: Annotated[User, Depends(require_organization_role(MemberRole.MEMBER))],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    data: TaskCreate,
) -> TaskResponse:
    """Create a new task in the indicated organization.

    Raises:
        HTTPException(400): Unable to create new task.
        HTTPException(403): User must be a member of the organization.
        HTTPException(404): Project not found.
    """
    try:
        async with transaction(task_service.session):
            task = await task_service.create_task(
                project_id=project_id, requesting_user=user, data=data
            )
        return TaskResponse.model_validate(task)
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be a member of the organization.",
        )
    except CreateTaskError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to create new task.")
    except ProjectNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")


# PATCH /api/v1/organizations/{org_id}/projects/{project_id}/tasks/{task_id}/status
@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    user: Annotated[User, Depends(require_organization_role(MemberRole.MEMBER))],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
) -> TaskResponse:
    """Update the status of a task.

    Raises:
        HTTPException(400): Can not update to the desired status.
        HTTPException(403): User must be a member of the organization.
        HTTPException(404): Task not found.
        HTTPException(404): Project not found.
    """
    try:
        async with transaction(task_service.session):
            task = await task_service.update_status(
                task_id=task_id, requesting_user=user, new_status=data.status
            )
        return TaskResponse.model_validate(task)

    except TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found.")
    except ProjectNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be a member of the organization.",
        )
    except InvalidTransitionError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Can not update to the desired status."
        )


# PATCH /api/v1/organizations/{org_id}/projects/{project_id}/tasks/{task_id}/assign
@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    user: Annotated[User, Depends(require_organization_role(MemberRole.MEMBER))],
    task_service: Annotated[TaskService, Depends(get_task_service)],
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    data: TaskAssigneeUpdate,
) -> TaskResponse:
    """Assign a task to a user from the organization.

    Raises:
        HTTPException(400): Assignee is not a member of the organization.
        HTTPException(403): User must be a member of the organization.
        HTTPException(404): Task not found.
        HTTPException(404): Project not found.
    """
    try:
        async with transaction(task_service.session):
            task = await task_service.assign_task(
                task_id=task_id, requesting_user=user, assignee_id=data.assignee_id
            )
        return TaskResponse.model_validate(task)

    except TaskNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found.")
    except ProjectNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be a member of the organization.",
        )
    except InvalidAssignee:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Assignee is not a member of the organization."
        )
