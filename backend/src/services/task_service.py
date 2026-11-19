import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task
from src.services.project_service import ProjectNotFoundError, ProjectService

TRASH_RETENTION = timedelta(days=30)
MIN_TITLE_LENGTH = 5  # FR-008
MAX_DESCRIPTION_LENGTH = 500  # FR-009


class TaskError(Exception):
    """Base class for task service errors."""


class TaskNotFoundError(TaskError):
    pass


class InvalidTaskTitleError(TaskError):
    pass


class InvalidTaskDescriptionError(TaskError):
    pass


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        project_service: ProjectService | None = None,
    ):
        self.session = session
        self.project_service = project_service or ProjectService(session)

    async def create(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str,
        description: str | None = None,
        upload_method: str | None = None,
    ) -> Task:
        await self.ensure_project_access(user_id, project_id)
        self.validate_title(title)
        self.validate_description(description)

        task_number = await self._next_task_number(project_id)
        task = Task(
            project_id=project_id,
            task_number=task_number,
            title=title,
            description=description,
            upload_method=upload_method,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = await self.session.get(Task, task_id)
        if task is None:
            raise TaskNotFoundError("Task not found")
        await self._ensure_owner(user_id, task.project_id)
        return task

    async def list_active(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[Task]:
        await self.ensure_project_access(user_id, project_id)
        result = await self.session.execute(
            select(Task)
            .where(Task.project_id == project_id, Task.deletion_status == "active")
            .order_by(Task.task_number.asc())
        )
        return list(result.scalars().all())

    async def update(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Task:
        task = await self._get_active_owned(user_id, task_id)
        if title is not None:
            self.validate_title(title)
            task.title = title
        if description is not None:
            self.validate_description(description)
            task.description = description
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def soft_delete(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = await self._get_active_owned(user_id, task_id)
        trashed_at = datetime.now(UTC)
        task.deletion_status = "trashed"
        task.trashed_at = trashed_at
        task.scheduled_deletion_at = trashed_at + TRASH_RETENTION
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def ensure_project_access(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> None:
        """Raise ProjectNotFoundError unless ``user_id`` owns an ACTIVE project
        with this id (missing, foreign, and trashed all look identical)."""
        project = await self.project_service.get(user_id=user_id, project_id=project_id)
        if project.deletion_status != "active":
            raise ProjectNotFoundError("Project not found")

    async def _ensure_owner(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        try:
            await self.project_service.get(user_id=user_id, project_id=project_id)
        except ProjectNotFoundError as exc:
            raise TaskNotFoundError("Task not found") from exc

    async def _get_active_owned(self, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        task = await self.session.get(Task, task_id)
        if task is None or task.deletion_status != "active":
            raise TaskNotFoundError("Task not found")
        await self._ensure_owner(user_id, task.project_id)
        return task

    async def _next_task_number(self, project_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.max(Task.task_number)).where(Task.project_id == project_id)
        )
        current_max = result.scalar()
        return (current_max or 0) + 1

    @staticmethod
    def validate_title(title: str) -> None:
        if not title or len(title.strip()) < MIN_TITLE_LENGTH:
            raise InvalidTaskTitleError(
                f"Title must be at least {MIN_TITLE_LENGTH} characters"
            )

    @staticmethod
    def validate_description(description: str | None) -> None:
        if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
            raise InvalidTaskDescriptionError(
                f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters"
            )
