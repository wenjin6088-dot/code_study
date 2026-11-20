"""T094: Celery task for async learning document generation.

The actual orchestration (load task's uploaded code -> call
DocumentGenerationService -> persist status transitions) lives in
``generate_document_async``, a pure async function with no Celery
dependency. ``generate_document_task`` is a thin synchronous wrapper that
Celery can run; it opens its own DB session and Gemini client and drives the
async core with ``asyncio.run(...)``.

This split lets T094's core logic be unit/integration tested without a
running Celery worker or a real Gemini API key.
"""

import asyncio
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal, engine
from src.models.code_file import CodeFile
from src.models.learning_document import LearningDocument

# Unused directly, but LearningDocument.task_id has a ForeignKey("tasks.id");
# a Celery worker process that only imports this module (never the API
# routers) never registers the "tasks" table otherwise, and flushing
# LearningDocument then fails with sqlalchemy.exc.NoReferencedTableError.
from src.models.task import Task  # noqa: F401
from src.models.uploaded_code import UploadedCode
from src.services.ai.gemini_client import GeminiClient
from src.services.ai.prompts import CodeFileInput
from src.services.code_analysis import file_storage
from src.services.document.document_generation_service import (
    DocumentGenerationService,
)
from src.tasks.celery_app import celery_app

DEFAULT_DETECTED_LANGUAGE = "unknown"
DEFAULT_COMPLEXITY_LEVEL = "beginner"

PracticeEnqueueFn = Callable[[uuid.UUID], None]


def _default_enqueue_practice(task_id: uuid.UUID) -> None:
    # T119: successful document generation triggers practice generation.
    from src.tasks.practice_generation import generate_practice_task

    generate_practice_task.delay(str(task_id))


class DocumentGenerationTaskError(Exception):
    """Base class for document generation task orchestration errors."""


class TaskCodeNotFoundError(DocumentGenerationTaskError):
    """Raised when the task has no LearningDocument row queued, or (inside
    the try/except of generate_document_async) no uploaded code to read."""


class DocumentServiceProtocol(Protocol):
    async def generate_document(
        self,
        files: list[CodeFileInput],
        *,
        detected_language: str,
        complexity_level: str,
    ) -> dict:
        ...


async def _get_document(
    session: AsyncSession, task_id: uuid.UUID
) -> LearningDocument | None:
    result = await session.execute(
        select(LearningDocument).where(LearningDocument.task_id == task_id)
    )
    return result.scalar_one_or_none()


async def _load_code_files(
    session: AsyncSession, task_id: uuid.UUID
) -> tuple[UploadedCode, list[CodeFileInput]]:
    result = await session.execute(
        select(UploadedCode).where(UploadedCode.task_id == task_id)
    )
    uploaded_code = result.scalar_one_or_none()
    if uploaded_code is None:
        raise TaskCodeNotFoundError(f"Task {task_id} has no uploaded code")

    files_result = await session.execute(
        select(CodeFile)
        .where(CodeFile.uploaded_code_id == uploaded_code.id)
        .order_by(CodeFile.file_name.asc())
    )
    code_files = list(files_result.scalars().all())
    inputs = [
        CodeFileInput(
            path=code_file.file_path or code_file.file_name,
            content=file_storage.read_file(code_file.storage_path).decode("utf-8"),
        )
        for code_file in code_files
    ]
    return uploaded_code, inputs


async def generate_document_async(
    task_id: uuid.UUID,
    session: AsyncSession,
    *,
    document_service: DocumentServiceProtocol,
    enqueue_practice: PracticeEnqueueFn | None = None,
) -> None:
    """Drive one task's document generation end to end and persist every
    status transition (FR-094: clear error message on terminal failure).

    Raises ``TaskCodeNotFoundError`` only when no ``LearningDocument`` row is
    queued for ``task_id`` at all (a genuine orchestration bug: T095 should
    always create one before enqueueing). Any failure that happens *after*
    the row is moved to ``in_progress`` (missing uploaded code, Gemini
    errors exhausted after retry, invalid document structure, ...) is
    captured and recorded on the row as ``failed`` instead of propagating.
    """
    document = await _get_document(session, task_id)
    if document is None:
        raise TaskCodeNotFoundError(
            f"Task {task_id} has no LearningDocument row queued"
        )

    document.generation_status = "in_progress"
    document.generation_started_at = datetime.now(UTC)
    document.generation_error = None
    await session.commit()

    try:
        _uploaded_code, files = await _load_code_files(session, task_id)
        content = await document_service.generate_document(
            files,
            detected_language=_uploaded_code.detected_language
            or DEFAULT_DETECTED_LANGUAGE,
            complexity_level=_uploaded_code.complexity_level
            or DEFAULT_COMPLEXITY_LEVEL,
        )
    except Exception as exc:  # noqa: BLE001 - this is the task's error boundary
        document.generation_status = "failed"
        document.generation_error = str(exc)
        document.generation_completed_at = datetime.now(UTC)
        await session.commit()
        return

    document.content = content
    document.generation_status = "completed"
    document.generation_completed_at = datetime.now(UTC)
    await session.commit()

    (enqueue_practice or _default_enqueue_practice)(task_id)


async def _run(task_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        service = DocumentGenerationService(GeminiClient())
        await generate_document_async(task_id, session, document_service=service)
    # The engine/pool is a module-level singleton shared across every
    # asyncio.run() call below, but each call gets a brand-new event loop.
    # asyncpg's pooled connections are bound to the loop they were opened
    # on, so a connection checked out under a later loop breaks (Windows
    # ProactorEventLoop: "AttributeError: 'NoneType' object has no
    # attribute 'send'"). Disposing after every run forces a fresh pool
    # for the next asyncio.run().
    await engine.dispose()


@celery_app.task(name="src.tasks.document_generation.generate_document_task")
def generate_document_task(task_id: str) -> None:
    """Celery entrypoint. Synchronous wrapper required because Celery tasks
    are sync, while the DB access and DocumentGenerationService are async."""
    asyncio.run(_run(uuid.UUID(task_id)))
