# src/projects/router.py
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.engine import get_db, transaction
from src.organizations.repository import MemberRole
from src.projects.schemas import ProjectCreate, ProjectList, ProjectResponse
from src.projects.service import (
    AlreadyArchived,
    CreateProjectError,
    ProjectNotFound,
    ProjectService,
)
from src.projects.ws_router import router as ws_router
from src.shared.dependencies import require_organization_role
from src.shared.exceptions import InsufficientPermissionError
from src.tasks.router import router as tasks_router
from src.users.models import User

router = APIRouter(prefix="/{org_id}/projects")
router.include_router(tasks_router)
router.include_router(ws_router)


def get_proj_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectService:
    return ProjectService(session=session)


@router.get("", response_model=ProjectList, tags=["projects"])
async def get_project_list(
    user: Annotated[User, Depends(require_organization_role(MemberRole.MEMBER))],
    proj_service: Annotated[ProjectService, Depends(get_proj_service)],
    org_id: uuid.UUID,
    limit: int,
    offset: int,
) -> ProjectList:
    """Obtain a wrapped list with the projects of an organization and
    the total amount.

    Raises:
        HTTPException(403): User must be at least a member of the
            organization.
    """
    try:
        items, total = await proj_service.list_projects(
            requesting_user=user, org_id=org_id, limit=limit, offset=offset
        )
        return ProjectList(
            items=[ProjectResponse.model_validate(p) for p in items], total=total
        )
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be at least a member of the organization.",
        )


@router.post("", response_model=ProjectResponse, tags=["projects"])
async def create_project(
    user: Annotated[User, Depends(require_organization_role(MemberRole.ADMIN))],
    proj_service: Annotated[ProjectService, Depends(get_proj_service)],
    org_id: uuid.UUID,
    data: ProjectCreate,
) -> ProjectResponse:
    """Create a new project in the indicated organization.

    Raises:
        HTTPException(400): Unable to create new project.
        HTTPException(403): User must be at least an admin of the
            organization.
    """
    try:
        async with transaction(proj_service.session):
            project = await proj_service.create_project(
                org_id=org_id, requesting_user=user, data=data
            )
        return ProjectResponse.model_validate(project)
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be at least an admin of the organization.",
        )
    except CreateProjectError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Unable to create new project."
        )


@router.patch(
    "/{project_id}/archive", response_model=ProjectResponse, tags=["projects"]
)
async def archive_project(
    user: Annotated[User, Depends(require_organization_role(MemberRole.ADMIN))],
    proj_service: Annotated[ProjectService, Depends(get_proj_service)],
    org_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ProjectResponse:
    """Archive an existing project.

    Raises:
        HTTPException(400): Project is already archived.
        HTTPException(403): User must be at least an admin of the
            organization.
        HTTPException(404): Project not found.
    """
    try:
        async with transaction(proj_service.session):
            project = await proj_service.archive_project(
                project_id=project_id, requesting_user=user
            )
        return ProjectResponse.model_validate(project)
    except ProjectNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    except InsufficientPermissionError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "User must be at least an admin of the organization.",
        )
    except AlreadyArchived:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project is already archived.")
