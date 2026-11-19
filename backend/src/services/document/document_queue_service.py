"""T095: document generation queue + status tracking service.

Owns the ``LearningDocument`` row's lifecycle from the API/trigger side:
creating it in ``pending`` status with a placeholder (but
constraint-satisfying) ``content``, enqueueing the Celery task (T094), and
answering "what's the current status" for T097/T098. The Celery task itself
owns moving the row through ``in_progress`` -> ``completed``/``failed``.
"""

import uuid
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.learning_document import LearningDocument
from src.services.ai.prompts import CHAPTER_KEYS

# learning_documents.valid_content_structure requires content to always
# carry all 7 chapter keys, even before generation has produced anything.
PLACEHOLDER_CONTENT = {key: {} for key in CHAPTER_KEYS}

# Statuses for which a generation run is already queued or running; a second
# enqueue request is a no-op so we don't duplicate Celery tasks.
_ACTIVE_STATUSES = {"pending", "in_progress"}

EnqueueFn = Callable[[uuid.UUID], str]


class DocumentQueueService:
    def __init__(self, session: AsyncSession, enqueue: EnqueueFn | None = None):
        self.session = session
        self._enqueue = enqueue or _default_enqueue

    async def enqueue_generation(self, task_id: uuid.UUID) -> LearningDocument:
        """Ensure a ``LearningDocument`` row exists for ``task_id`` and
        enqueue the Celery generation task for it.

        Idempotent while a run is already queued/running: calling this again
        for the same task returns the existing row without re-enqueueing.
        After a terminal state (``completed``/``failed``) it resets the row
        to ``pending`` and enqueues a fresh run (manual retry, FR-094).
        """
        document = await self._get(task_id)
        if document is not None and document.generation_status in _ACTIVE_STATUSES:
            return document

        if document is None:
            document = LearningDocument(
                task_id=task_id,
                content=PLACEHOLDER_CONTENT,
                generation_status="pending",
            )
            self.session.add(document)
        else:
            document.content = PLACEHOLDER_CONTENT
            document.generation_status = "pending"
            document.generation_error = None
            document.generation_started_at = None
            document.generation_completed_at = None

        await self.session.commit()
        await self.session.refresh(document)

        document.celery_task_id = self._enqueue(task_id)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_status(self, task_id: uuid.UUID) -> LearningDocument | None:
        return await self._get(task_id)

    async def _get(self, task_id: uuid.UUID) -> LearningDocument | None:
        result = await self.session.execute(
            select(LearningDocument).where(LearningDocument.task_id == task_id)
        )
        return result.scalar_one_or_none()


def _default_enqueue(task_id: uuid.UUID) -> str:
    from src.tasks.document_generation import generate_document_task

    async_result = generate_document_task.delay(str(task_id))
    return async_result.id
