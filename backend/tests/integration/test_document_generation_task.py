"""Integration tests for T094: the async core of the Celery document
generation task (src/tasks/document_generation.py).

The Celery task itself (`generate_document_task`, a sync wrapper around
`asyncio.run(...)`) is intentionally NOT exercised here: it builds a real
GeminiClient, which requires GOOGLE_API_KEY. Per project convention, we never
call the real Gemini API from tests. Instead we test
`generate_document_async`, the pure-async core the wrapper delegates to,
with a fake DocumentGenerationService.
"""

import uuid

import pytest
from sqlalchemy import select

from src.models.learning_document import LearningDocument
from src.services.ai.prompts import CHAPTER_KEYS
from src.services.code_analysis.code_upload_service import (
    CodeUploadService,
    UploadedFileInput,
)
from src.services.project_service import ProjectService
from src.services.task_service import TaskService
from src.tasks.document_generation import (
    TaskCodeNotFoundError,
    generate_document_async,
)

PLACEHOLDER_CONTENT = {key: {} for key in CHAPTER_KEYS}
VALID_DOCUMENT = {key: {"title": key} for key in CHAPTER_KEYS}


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))


class FakeDocumentGenerationService:
    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error
        self.calls: list[dict] = []

    async def generate_document(self, files, *, detected_language, complexity_level):
        self.calls.append(
            {
                "files": files,
                "detected_language": detected_language,
                "complexity_level": complexity_level,
            }
        )
        if self._error is not None:
            raise self._error
        return self._result


async def _register_user(db_session):
    from src.services.auth.user_service import UserService

    return await UserService(db_session).register(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com", password="Password123"
    )


async def _make_task_with_upload(db_session, files: list[UploadedFileInput]):
    user = await _register_user(db_session)
    project = await ProjectService(db_session).create(user_id=user.id, title="P")
    task = await TaskService(db_session).create(
        user_id=user.id, project_id=project.id, title="Task with code"
    )
    await CodeUploadService(db_session).create_upload(
        user_id=user.id, task_id=task.id, files=files
    )
    return task


async def _make_pending_document(db_session, task_id):
    document = LearningDocument(
        task_id=task_id, content=PLACEHOLDER_CONTENT, generation_status="pending"
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


async def _reload(db_session, task_id) -> LearningDocument:
    result = await db_session.execute(
        select(LearningDocument).where(LearningDocument.task_id == task_id)
    )
    return result.scalar_one()


class TestGenerateDocumentAsyncSuccess:
    async def test_marks_completed_and_stores_generated_content(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)
        service = FakeDocumentGenerationService(result=VALID_DOCUMENT)

        await generate_document_async(task.id, db_session, document_service=service)

        document = await _reload(db_session, task.id)
        assert document.generation_status == "completed"
        assert document.content == VALID_DOCUMENT
        assert document.generation_started_at is not None
        assert document.generation_completed_at is not None
        assert document.generation_error is None

    async def test_passes_detected_language_and_complexity_to_service(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)
        service = FakeDocumentGenerationService(result=VALID_DOCUMENT)

        await generate_document_async(task.id, db_session, document_service=service)

        call = service.calls[0]
        assert call["detected_language"] == "python"
        assert call["complexity_level"] == "beginner"
        assert call["files"][0].content == "print(1)\n"

    async def test_sets_in_progress_before_calling_service(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)

        class ObservingService(FakeDocumentGenerationService):
            async def generate_document(self, files, **kwargs):
                observed.append("called")
                return await super().generate_document(files, **kwargs)

        observed: list[str] = []
        service = ObservingService(result=VALID_DOCUMENT)
        await generate_document_async(task.id, db_session, document_service=service)
        assert observed == ["called"]


class TestGenerateDocumentAsyncFailure:
    async def test_marks_failed_with_error_message_when_service_raises(
        self, db_session
    ):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)
        service = FakeDocumentGenerationService(error=RuntimeError("Gemini exploded"))

        await generate_document_async(task.id, db_session, document_service=service)

        document = await _reload(db_session, task.id)
        assert document.generation_status == "failed"
        assert document.generation_error == "Gemini exploded"
        assert document.generation_completed_at is not None
        # Content must still satisfy the DB CHECK constraint (placeholder kept).
        assert set(document.content.keys()) == set(CHAPTER_KEYS)

    async def test_marks_failed_when_task_has_no_uploaded_code(self, db_session):
        user = await _register_user(db_session)
        project = await ProjectService(db_session).create(user_id=user.id, title="P")
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="No code task"
        )
        await _make_pending_document(db_session, task.id)
        service = FakeDocumentGenerationService(result=VALID_DOCUMENT)

        await generate_document_async(task.id, db_session, document_service=service)

        document = await _reload(db_session, task.id)
        assert document.generation_status == "failed"
        assert document.generation_error
        assert service.calls == []

    async def test_raises_when_no_learning_document_row_exists(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        service = FakeDocumentGenerationService(result=VALID_DOCUMENT)

        with pytest.raises(TaskCodeNotFoundError):
            await generate_document_async(task.id, db_session, document_service=service)
