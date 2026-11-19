import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import NotFoundError
from src.db.session import get_db
from src.models.learning_document import LearningDocument
from src.models.user import User
from src.services.document.document_queue_service import DocumentQueueService
from src.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(tags=["documents"])

# FR-083: target end-to-end document generation time, used only to give the
# client a rough ETA while a generation run is in progress.
TARGET_GENERATION_SECONDS = 180


class DocumentResponse(BaseModel):
    task_id: str
    status: str
    content: dict[str, Any] | None
    error: str | None
    generated_at: str | None


class DocumentStatusResponse(BaseModel):
    status: str
    error: str | None
    estimated_seconds_remaining: float | None


async def _get_owned_document(
    task_id: uuid.UUID, user: User, session: AsyncSession
) -> LearningDocument:
    try:
        task = await TaskService(session).get(user_id=user.id, task_id=task_id)
    except TaskNotFoundError as exc:
        raise NotFoundError("Task not found") from exc

    document = await DocumentQueueService(session).get_status(task.id)
    if document is None:
        raise NotFoundError("Learning document not found")
    return document


def _estimated_seconds_remaining(document: LearningDocument) -> float | None:
    if document.generation_status != "in_progress":
        return None
    if document.generation_started_at is None:
        return None
    elapsed = (datetime.now(UTC) - document.generation_started_at).total_seconds()
    return max(TARGET_GENERATION_SECONDS - elapsed, 0.0)


@router.get("/tasks/{task_id}/document")
async def get_document(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    document = await _get_owned_document(task_id, user, session)
    is_completed = document.generation_status == "completed"
    is_failed = document.generation_status == "failed"
    return DocumentResponse(
        task_id=str(task_id),
        status=document.generation_status,
        content=document.content if is_completed else None,
        error=document.generation_error if is_failed else None,
        generated_at=(
            document.generation_completed_at.isoformat()
            if is_completed and document.generation_completed_at
            else None
        ),
    )


@router.get("/tasks/{task_id}/document/status")
async def get_document_status(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    document = await _get_owned_document(task_id, user, session)
    is_failed = document.generation_status == "failed"
    return DocumentStatusResponse(
        status=document.generation_status,
        error=document.generation_error if is_failed else None,
        estimated_seconds_remaining=_estimated_seconds_remaining(document),
    )
