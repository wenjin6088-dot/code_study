"""T118: Celery task for async practice problem generation.

Mirrors document_generation.py's split: ``generate_practice_async`` is a pure
async function with no Celery dependency (unit/integration testable without a
running worker or a real Gemini API key), and ``generate_practice_task`` is
the thin synchronous Celery entrypoint around it.

Unlike LearningDocument, practice_problems has no status/error column (see
data-model.md): there is nothing to mark "pending"/"failed". So this task
either inserts all 5 problems on success, or inserts nothing and logs the
failure - it never raises out of the Celery task.
"""

import asyncio
import logging
import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal, engine
from src.models.code_file import CodeFile
from src.models.practice_problem import PracticeProblem

# Unused directly, but PracticeProblem.task_id has a ForeignKey("tasks.id");
# a Celery worker process that only imports this module never registers the
# "tasks" table otherwise (see document_generation.py for the same issue).
from src.models.task import Task  # noqa: F401
from src.models.uploaded_code import UploadedCode
from src.services.ai.gemini_client import GeminiClient
from src.services.ai.prompts import CodeFileInput
from src.services.code_analysis import file_storage
from src.services.practice.practice_generation_service import (
    PracticeGenerationService,
)
from src.tasks.celery_app import celery_app

DEFAULT_DETECTED_LANGUAGE = "unknown"
DEFAULT_COMPLEXITY_LEVEL = "beginner"

logger = logging.getLogger(__name__)


class PracticeServiceProtocol(Protocol):
    async def generate_problems(
        self,
        files: list[CodeFileInput],
        *,
        detected_language: str,
        complexity_level: str,
    ) -> list[dict]:
        ...


async def _load_code_files(
    session: AsyncSession, task_id: uuid.UUID
) -> tuple[UploadedCode, list[CodeFileInput]]:
    result = await session.execute(
        select(UploadedCode).where(UploadedCode.task_id == task_id)
    )
    uploaded_code = result.scalar_one_or_none()
    if uploaded_code is None:
        raise ValueError(f"Task {task_id} has no uploaded code")

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


async def _has_existing_problems(session: AsyncSession, task_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(PracticeProblem.id).where(PracticeProblem.task_id == task_id).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def generate_practice_async(
    task_id: uuid.UUID,
    session: AsyncSession,
    *,
    practice_service: PracticeServiceProtocol,
) -> None:
    """Generate and persist the 5 practice problems for ``task_id``.

    Idempotent: a no-op if problems already exist for this task. On any
    failure (missing uploaded code, Gemini errors exhausted after retry,
    invalid structure, ...) the failure is logged and no rows are inserted -
    this never raises, since it runs from a Celery task with nothing in the
    schema to record a "failed" status against.
    """
    if await _has_existing_problems(session, task_id):
        return

    try:
        _uploaded_code, files = await _load_code_files(session, task_id)
        problems = await practice_service.generate_problems(
            files,
            detected_language=_uploaded_code.detected_language
            or DEFAULT_DETECTED_LANGUAGE,
            complexity_level=_uploaded_code.complexity_level
            or DEFAULT_COMPLEXITY_LEVEL,
        )
    except Exception:  # noqa: BLE001 - this is the task's error boundary
        logger.exception("Practice generation failed for task %s", task_id)
        return

    for problem in problems:
        session.add(
            PracticeProblem(
                task_id=task_id,
                problem_number=problem["problem_number"],
                problem_type=problem["problem_type"],
                problem_statement=problem["problem_statement"],
                learning_objective=problem.get("learning_objective"),
                hints=problem.get("hints"),
                model_solution=problem.get("model_solution"),
                expected_output=problem.get("expected_output"),
            )
        )
    await session.commit()


async def _run(task_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        service = PracticeGenerationService(GeminiClient())
        await generate_practice_async(task_id, session, practice_service=service)
    # See the matching comment in document_generation.py's _run: dispose the
    # shared engine's pool so the next asyncio.run() in this worker process
    # doesn't reuse a connection bound to a now-closed event loop.
    await engine.dispose()


@celery_app.task(name="src.tasks.practice_generation.generate_practice_task")
def generate_practice_task(task_id: str) -> None:
    """Celery entrypoint. Synchronous wrapper required because Celery tasks
    are sync, while the DB access and PracticeGenerationService are async."""
    asyncio.run(_run(uuid.UUID(task_id)))
