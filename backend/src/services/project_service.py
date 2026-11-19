import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project

TRASH_RETENTION = timedelta(days=30)


class ProjectError(Exception):
    """Base class for project service errors."""


class ProjectNotFoundError(ProjectError):
    pass


class InvalidProjectTitleError(ProjectError):
    pass


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: uuid.UUID, title: str, description: str | None = None
    ) -> Project:
        self._validate_title(title)
        project = Project(user_id=user_id, title=title, description=description)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id, Project.user_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError("Project not found")
        return project

    async def list_active(self, user_id: uuid.UUID) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(
                Project.user_id == user_id, Project.deletion_status == "active"
            )
        )
        return list(result.scalars().all())

    async def update(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Project:
        project = await self._get_active(user_id, project_id)
        if title is not None:
            self._validate_title(title)
            project.title = title
        if description is not None:
            project.description = description
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def soft_delete(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        project = await self._get_active(user_id, project_id)
        trashed_at = datetime.now(UTC)
        project.deletion_status = "trashed"
        project.trashed_at = trashed_at
        project.scheduled_deletion_at = trashed_at + TRASH_RETENTION
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def _get_active(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deletion_status == "active",
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError("Project not found")
        return project

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise InvalidProjectTitleError("Title must not be empty")
