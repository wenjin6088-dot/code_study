import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import NotFoundError
from src.db.session import get_db
from src.models.project import Project
from src.models.user import User
from src.services.project_service import ProjectNotFoundError
from src.services.trash_service import TrashService

router = APIRouter(prefix="/trash", tags=["trash"])


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str | None
    deletion_status: str

    model_config = {"from_attributes": True}


class TrashListResponse(BaseModel):
    projects: list[ProjectResponse]


def _project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        title=project.title,
        description=project.description,
        deletion_status=project.deletion_status,
    )


@router.get("")
async def list_trash(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TrashListResponse:
    projects = await TrashService(session).list_trashed_projects(user_id=user.id)
    return TrashListResponse(projects=[_project_response(p) for p in projects])


@router.post("/projects/{project_id}/restore")
async def restore_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await TrashService(session).restore_project(
            user_id=user.id, project_id=project_id
        )
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    return _project_response(project)


@router.delete(
    "/projects/{project_id}/permanent-delete",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def permanent_delete_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    try:
        await TrashService(session).permanent_delete_project(
            user_id=user.id, project_id=project_id
        )
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
