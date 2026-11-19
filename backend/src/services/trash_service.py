import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.project import Project
from src.services.project_service import ProjectNotFoundError


class TrashService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_trashed_projects(self, user_id: uuid.UUID) -> list[Project]:
        result = await self.session.execute(
            select(Project).where(
                Project.user_id == user_id, Project.deletion_status == "trashed"
            )
        )
        return list(result.scalars().all())

    async def restore_project(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> Project:
        project = await self._get_trashed(user_id, project_id)
        project.deletion_status = "active"
        project.trashed_at = None
        project.scheduled_deletion_at = None
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def permanent_delete_project(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> None:
        project = await self._get_trashed(user_id, project_id)
        await self.session.delete(project)
        await self.session.commit()

    async def _get_trashed(self, user_id: uuid.UUID, project_id: uuid.UUID) -> Project:
        result = await self.session.execute(
            select(Project).where(
                Project.id == project_id,
                Project.user_id == user_id,
                Project.deletion_status == "trashed",
            )
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ProjectNotFoundError("Project not found")
        return project
