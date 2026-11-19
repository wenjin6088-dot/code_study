"""Integration tests for T095: DocumentQueueService (queue + status tracking).

Real DB (`db_session`), fake `enqueue` callable so no Celery/Redis call is
made from these tests.
"""

import uuid

from src.services.ai.prompts import CHAPTER_KEYS
from src.services.document.document_queue_service import DocumentQueueService
from src.services.project_service import ProjectService
from src.services.task_service import TaskService

PLACEHOLDER_CONTENT = {key: {} for key in CHAPTER_KEYS}


class FakeEnqueue:
    """Records calls and returns a deterministic fake celery task id."""

    def __init__(self):
        self.calls: list[uuid.UUID] = []

    def __call__(self, task_id: uuid.UUID) -> str:
        self.calls.append(task_id)
        return f"fake-celery-task-{len(self.calls)}"


async def _register_user(db_session):
    from src.services.auth.user_service import UserService

    return await UserService(db_session).register(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com", password="Password123"
    )


async def _make_task(db_session):
    user = await _register_user(db_session)
    project = await ProjectService(db_session).create(user_id=user.id, title="P")
    return await TaskService(db_session).create(
        user_id=user.id, project_id=project.id, title="Queueable task"
    )


class TestEnqueueGeneration:
    async def test_creates_pending_document_with_placeholder_content(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)

        document = await service.enqueue_generation(task.id)

        assert document.task_id == task.id
        assert document.generation_status == "pending"
        assert document.content == PLACEHOLDER_CONTENT

    async def test_calls_enqueue_fn_and_stores_celery_task_id(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)

        document = await service.enqueue_generation(task.id)

        assert enqueue.calls == [task.id]
        assert document.celery_task_id == "fake-celery-task-1"

    async def test_is_idempotent_while_pending(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)

        first = await service.enqueue_generation(task.id)
        second = await service.enqueue_generation(task.id)

        assert len(enqueue.calls) == 1
        assert first.id == second.id

    async def test_is_idempotent_while_in_progress(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)
        document = await service.enqueue_generation(task.id)
        document.generation_status = "in_progress"
        await db_session.commit()

        await service.enqueue_generation(task.id)

        assert len(enqueue.calls) == 1

    async def test_reenqueues_after_failed_status(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)
        document = await service.enqueue_generation(task.id)
        document.generation_status = "failed"
        document.generation_error = "boom"
        await db_session.commit()

        retried = await service.enqueue_generation(task.id)

        assert len(enqueue.calls) == 2
        assert retried.generation_status == "pending"
        assert retried.generation_error is None
        assert retried.content == PLACEHOLDER_CONTENT

    async def test_reenqueues_after_completed_status(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)
        document = await service.enqueue_generation(task.id)
        document.generation_status = "completed"
        document.content = {k: {"title": k} for k in CHAPTER_KEYS}
        await db_session.commit()

        retried = await service.enqueue_generation(task.id)

        assert len(enqueue.calls) == 2
        assert retried.generation_status == "pending"


class TestGetStatus:
    async def test_returns_none_without_document(self, db_session):
        task = await _make_task(db_session)
        service = DocumentQueueService(db_session, enqueue=FakeEnqueue())

        result = await service.get_status(task.id)

        assert result is None

    async def test_returns_existing_document(self, db_session):
        task = await _make_task(db_session)
        enqueue = FakeEnqueue()
        service = DocumentQueueService(db_session, enqueue=enqueue)
        created = await service.enqueue_generation(task.id)

        result = await service.get_status(task.id)

        assert result.id == created.id
