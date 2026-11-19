"""Integration tests for:
- T118: the async core of the Celery practice generation task
  (src/tasks/practice_generation.py)
- T119: document generation auto-triggers practice generation on success
  (src/tasks/document_generation.py)

The Celery task itself is intentionally NOT exercised here for the same
reason as test_document_generation_task.py: it builds a real GeminiClient,
which requires GOOGLE_API_KEY. We test the pure-async core instead, with a
fake PracticeGenerationService.
"""

import uuid

import pytest
from sqlalchemy import select

from src.models.learning_document import LearningDocument
from src.models.practice_problem import PracticeProblem
from src.services.ai.prompts import CHAPTER_KEYS, PRACTICE_PROBLEM_TYPES
from src.services.code_analysis.code_upload_service import (
    CodeUploadService,
    UploadedFileInput,
)
from src.services.project_service import ProjectService
from src.services.task_service import TaskService
from src.tasks.document_generation import generate_document_async
from src.tasks.practice_generation import generate_practice_async

PLACEHOLDER_CONTENT = {key: {} for key in CHAPTER_KEYS}
VALID_DOCUMENT = {key: {"title": key} for key in CHAPTER_KEYS}


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))


def _valid_problems() -> list[dict]:
    return [
        {
            "problem_number": number,
            "problem_type": problem_type,
            "problem_statement": f"Statement {number}",
            "learning_objective": f"Objective {number}",
            "hints": ["Hint 1", "Hint 2"],
            "model_solution": f"Solution {number}",
            "expected_output": f"Output {number}",
        }
        for number, problem_type in enumerate(PRACTICE_PROBLEM_TYPES, 1)
    ]


class FakePracticeGenerationService:
    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error
        self.calls: list[dict] = []

    async def generate_problems(self, files, *, detected_language, complexity_level):
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


class FakeDocumentGenerationService:
    def __init__(self, result=None):
        self._result = result

    async def generate_document(self, files, *, detected_language, complexity_level):
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
    return document


async def _practice_problems(db_session, task_id) -> list[PracticeProblem]:
    result = await db_session.execute(
        select(PracticeProblem)
        .where(PracticeProblem.task_id == task_id)
        .order_by(PracticeProblem.problem_number.asc())
    )
    return list(result.scalars().all())


class TestGeneratePracticeAsyncSuccess:
    async def test_inserts_five_problems_ordered_by_number(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        service = FakePracticeGenerationService(result=_valid_problems())

        await generate_practice_async(task.id, db_session, practice_service=service)

        problems = await _practice_problems(db_session, task.id)
        assert [p.problem_number for p in problems] == [1, 2, 3, 4, 5]
        assert [p.problem_type for p in problems] == list(PRACTICE_PROBLEM_TYPES)
        assert problems[0].problem_statement == "Statement 1"
        assert problems[0].hints == ["Hint 1", "Hint 2"]

    async def test_passes_detected_language_and_complexity_to_service(
        self, db_session
    ):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        service = FakePracticeGenerationService(result=_valid_problems())

        await generate_practice_async(task.id, db_session, practice_service=service)

        call = service.calls[0]
        assert call["detected_language"] == "python"
        assert call["complexity_level"] == "beginner"

    async def test_is_idempotent_when_problems_already_exist(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        service = FakePracticeGenerationService(result=_valid_problems())
        await generate_practice_async(task.id, db_session, practice_service=service)

        await generate_practice_async(task.id, db_session, practice_service=service)

        assert len(service.calls) == 1
        problems = await _practice_problems(db_session, task.id)
        assert len(problems) == 5


class TestGeneratePracticeAsyncFailure:
    async def test_inserts_nothing_when_service_raises(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        service = FakePracticeGenerationService(error=RuntimeError("Gemini exploded"))

        await generate_practice_async(task.id, db_session, practice_service=service)

        problems = await _practice_problems(db_session, task.id)
        assert problems == []

    async def test_inserts_nothing_when_task_has_no_uploaded_code(self, db_session):
        user = await _register_user(db_session)
        project = await ProjectService(db_session).create(user_id=user.id, title="P")
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="No code task"
        )
        service = FakePracticeGenerationService(result=_valid_problems())

        await generate_practice_async(task.id, db_session, practice_service=service)

        problems = await _practice_problems(db_session, task.id)
        assert problems == []
        assert service.calls == []


class TestPracticeTriggeredAfterDocumentGeneration:
    async def test_enqueues_practice_generation_on_document_success(self, db_session):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)
        document_service = FakeDocumentGenerationService(result=VALID_DOCUMENT)
        enqueued: list[uuid.UUID] = []

        await generate_document_async(
            task.id,
            db_session,
            document_service=document_service,
            enqueue_practice=enqueued.append,
        )

        assert enqueued == [task.id]

    async def test_does_not_enqueue_practice_generation_on_document_failure(
        self, db_session
    ):
        task = await _make_task_with_upload(
            db_session, [UploadedFileInput(filename="main.py", content=b"print(1)\n")]
        )
        await _make_pending_document(db_session, task.id)

        class FailingDocumentService:
            async def generate_document(self, files, **kwargs):
                raise RuntimeError("boom")

        enqueued: list[uuid.UUID] = []

        await generate_document_async(
            task.id,
            db_session,
            document_service=FailingDocumentService(),
            enqueue_practice=enqueued.append,
        )

        assert enqueued == []
