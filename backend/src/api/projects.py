import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import AppException, NotFoundError
from src.db.session import get_db
from src.models.project import Project
from src.models.user import User
from src.services.project_service import (
    InvalidProjectTitleError,
    ProjectNotFoundError,
    ProjectService,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    title: str
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    description: str | None
    deletion_status: str

    model_config = {"from_attributes": True}


def _project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        title=project.title,
        description=project.description,
        deletion_status=project.deletion_status,
    )


@router.get("")
async def list_projects(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    projects = await ProjectService(session).list_active(user_id=user.id)
    return [_project_response(p) for p in projects]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await ProjectService(session).create(
            user_id=user.id, title=payload.title, description=payload.description
        )
    except InvalidProjectTitleError as exc:
        raise AppException(str(exc)) from exc
    return _project_response(project)


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await ProjectService(session).get(
            user_id=user.id, project_id=project_id
        )
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    return _project_response(project)


@router.patch("/{project_id}")
async def update_project(
    project_id: uuid.UUID,
    payload: UpdateProjectRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await ProjectService(session).update(
            user_id=user.id,
            project_id=project_id,
            title=payload.title,
            description=payload.description,
        )
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except InvalidProjectTitleError as exc:
        raise AppException(str(exc)) from exc
    return _project_response(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    try:
        project = await ProjectService(session).soft_delete(
            user_id=user.id, project_id=project_id
        )
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    return _project_response(project)
