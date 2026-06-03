# src/tasks/service.py
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.organizations.permissions import check_role
from src.organizations.repository import MemberRole, OrganizationMemberRepository
from src.projects.repository import ProjectRepository
from src.projects.service import ProjectService
from src.shared.exceptions import InsufficientPermissionError
from src.tasks.models import Task, TaskStatus
from src.tasks.repository import TaskRepository
from src.tasks.schemas import (
    TaskCreate,
)
from src.tasks.state_machine import validate_transition
from src.users.models import User


# Exceptions
class CreateTaskError(Exception): ...


class TaskNotFound(Exception): ...


class InvalidAssignee(Exception): ...


# Services
class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.proj_service = ProjectService(session)
        self.member_repo = OrganizationMemberRepository(session)
        self.proj_repo = ProjectRepository(session)

    async def create_task(
        self, project_id: uuid.UUID, requesting_user: User, data: TaskCreate
    ) -> Task:
        """Create new task.

        Args:
            project_id: uuid of the task.
            requesting_user: user creating the task.
            data: information about the new task.

        Returns:
            New task model.

        Raises:
            ProjectNotFound: if the project associated to the task
                does not exist.
            InsufficientPermissionError: if the requesting user is not
                a member of the organization.
            CreateTaskError: if the creation of the task fails.
        """
        project = await self.proj_service.get_project(project_id=project_id)

        await check_role(
            member_repo=self.member_repo,
            user_id=requesting_user.id,
            organization_id=project.organization_id,
            min_role=MemberRole.MEMBER,
        )

        try:
            new_task = Task(
                project_id=project_id,
                **data.model_dump(exclude_none=True),
            )
            return await self.task_repo.create(new_task)
        except IntegrityError as e:
            raise CreateTaskError(f"Unable to create new project: {e}.")

    async def update_status(
        self, task_id: uuid.UUID, requesting_user: User, new_status: TaskStatus
    ) -> Task:
        """Update the status of a task.

        Args:
            task_id: uuid of the task.
            requesting_user: user updating the task.
            new_status: desired new status.

        Returns:
            Updated task model.

        Raises:
            TaskNotFound: if the task doesn't exist.
            ProjectNotFound: if the project associated to the task
                does not exist.
            InsufficientPermissionError: if the requesting user is not
                a member of the organization.
            InvalidTransitionError: if the requested transition is not
                valid.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFound("The task doesn't exist.")

        project = await self.proj_service.get_project(project_id=task.project_id)

        await check_role(
            member_repo=self.member_repo,
            user_id=requesting_user.id,
            organization_id=project.organization_id,
            min_role=MemberRole.MEMBER,
        )

        validate_transition(current_status=task.status, next_status=new_status)

        task.status = new_status
        await self.session.flush()
        return task

    async def assign_task(
        self, task_id: uuid.UUID, requesting_user: User, assignee_id: uuid.UUID
    ) -> Task:
        """Assign the task to an organization member.

        Args:
            task_id: uuid of the task.
            requesting_user: user assigning the task.
            assignee_id: uuid of the user to whom assign the task.

        Returns:
            Updated task model.

        Raises:
            TaskNotFound: if the task doesn't exist.
            ProjectNotFound: if the project associated to the task
                does not exist.
            InsufficientPermissionError: if the requesting user is not
                a member of the organization.
            InvalidAssignee: if the assignee is not member of the
                organization.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise TaskNotFound("The task doesn't exist.")

        project = await self.proj_service.get_project(project_id=task.project_id)

        await check_role(
            member_repo=self.member_repo,
            user_id=requesting_user.id,
            organization_id=project.organization_id,
            min_role=MemberRole.MEMBER,
        )

        try:
            await check_role(
                member_repo=self.member_repo,
                user_id=assignee_id,
                organization_id=project.organization_id,
                min_role=MemberRole.MEMBER,
            )
        except InsufficientPermissionError:
            raise InvalidAssignee("Assignee is not a valid member of the organization")

        task.assignee_id = assignee_id
        await self.session.flush()
        return task

    async def list_tasks(
        self, requesting_user: User, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """Return a wrapped list of a project's tasks.

        Args:
            requesting_user: user requesting the list.
            project_id: uuid of the project.
            limit: max number of tasks to return.
            offset: number of tasks to skip from the beginning of the
                list.

        Returns:
            Tuple containing a wrapped list of tasks and the total
            amount of tasks of the project

        Raises:
            ProjectNotFound: if the project associated to the task
                does not exist.
            InsufficientPermissionError: if the user is not at least a
                member of the organization.
        """
        project = await self.proj_service.get_project(project_id=project_id)

        await check_role(
            member_repo=self.member_repo,
            user_id=requesting_user.id,
            organization_id=project.organization_id,
            min_role=MemberRole.MEMBER,
        )

        task_list = await self.task_repo.get_by_project(
            proj_id=project_id, limit=limit, offset=offset
        )
        total = await self.task_repo.count_by_project(proj_id=project_id)

        return (task_list, total)
