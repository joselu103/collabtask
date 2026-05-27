# src/projects/service.py
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.organizations.repository import (
    MemberRole,
    OrganizationMemberRepository,
)
from src.projects.models import Project
from src.projects.repository import ProjectRepository
from src.projects.schemas import ProjectCreate
from src.shared.exceptions import InsufficientPermissionError
from src.users.models import User


# Exceptions
class CreateProjectError(Exception): ...


class ProjectNotFound(Exception): ...


class AlreadyArchived(Exception): ...


# Services
class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.proj_repo = ProjectRepository(session)
        self.member_repo = OrganizationMemberRepository(session)

    async def _check_role(
        self, user_id: uuid.UUID, organization_id: uuid.UUID, min_role: MemberRole
    ) -> None:
        requesting_member = await self.member_repo.get_by_user_and_organization_ids(
            user_id=user_id, organization_id=organization_id
        )

        if not requesting_member or requesting_member.role < min_role:
            raise InsufficientPermissionError(
                f"User must be at least a {min_role} of the organization."
            )

    async def create_project(
        self, org_id: uuid.UUID, requesting_user: User, data: ProjectCreate
    ) -> Project:
        """Create new project.

        The requesting user must be at least an admin of the organization.

        Args:
            org_id: uuid of the organization.
            requesting_user: user creating the project.
            data: information about the new project.

        Returns:
            New project model.

        Raises:
            InsufficientPermissionError: if the user is not at least an
                admin of the organization.
            CreateProjectError: if the creation of the project fails.
        """
        await self._check_role(
            user_id=requesting_user.id,
            organization_id=org_id,
            min_role=MemberRole.ADMIN,
        )

        try:
            new_project = Project(organization_id=org_id, **data.model_dump())
            return await self.proj_repo.create(new_project)
        except IntegrityError as e:
            raise CreateProjectError(f"Unable to create new project: {e}.")

    async def archive_project(
        self, project_id: uuid.UUID, requesting_user: User
    ) -> Project:
        """Archive a project.

        The requesting user must be at least an admin of the organization.

        Args:
            project_id: uuid of the project.
            requesting_user: user requesting the change.

        Returns:
            Archived project model.

        Raises:
            ProjectNotFound: if the project doesn't exist.
            AlreadyArchived: if the project is already archived.
            InsufficientPermissionError: if the user is not at least an
                admin of the organization.
        """
        project = await self.proj_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFound("The project doesn't exist.")

        if project.is_archived:
            raise AlreadyArchived("The project is already archived")

        await self._check_role(
            user_id=requesting_user.id,
            organization_id=project.organization_id,
            min_role=MemberRole.ADMIN,
        )

        project.is_archived = True
        return project

    async def list_projects(
        self, requesting_user: User, org_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        """Return a wrapped list of an organization's projects.

        Args:
            requesting_user: user requesting the list.
            org_id: uuid of the organization.
            limit: max number of projects to return.
            offset: number of projects to skip from the beginning of the
                list.

        Returns:
            Tuple containing a wrapped list of projects and the total
            amount of projects of the organization

        Raises:
            InsufficientPermissionError: if the user is not at least a
                member of the organization.
        """
        await self._check_role(
            user_id=requesting_user.id,
            organization_id=org_id,
            min_role=MemberRole.MEMBER,
        )
        project_list = await self.proj_repo.get_by_organization(
            org_id=org_id, limit=limit, offset=offset
        )
        total = await self.proj_repo.count_by_organization(org_id=org_id)

        return (project_list, total)
