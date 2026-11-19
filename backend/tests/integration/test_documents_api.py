"""Integration tests for:
- T096: document generation auto-triggered right after a successful code
  upload in POST /api/v1/projects/{project_id}/tasks
- T097: GET /api/v1/tasks/{task_id}/document
- T098: GET /api/v1/tasks/{task_id}/document/status

Reuses the auth/client/project helpers from test_tasks_api.py.
"""

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select

from src.db.session import get_db
from src.main import app
from src.models.learning_document import LearningDocument
from src.services.ai.prompts import CHAPTER_KEYS
from src.services.task_service import TaskService
from tests.integration.test_tasks_api import (
    authenticated_client,
    create_project,
    register_via_service,
)

PLACEHOLDER_CONTENT = {key: {} for key in CHAPTER_KEYS}
VALID_DOCUMENT = {key: {"title": key} for key in CHAPTER_KEYS}


@pytest.fixture(autouse=True)
def _jwt_secrets(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


async def _make_task_without_upload(db_session, user):
    project = await create_project(db_session, user.id)
    return await TaskService(db_session).create(
        user_id=user.id, project_id=project.id, title="No code task"
    )


async def _insert_document(db_session, task_id, **overrides) -> LearningDocument:
    defaults = {"content": PLACEHOLDER_CONTENT, "generation_status": "pending"}
    defaults.update(overrides)
    document = LearningDocument(task_id=task_id, **defaults)
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


# ---------------------------------------------------------------------------
# T096: auto-trigger after code upload
# ---------------------------------------------------------------------------


class TestDocumentGenerationTriggeredOnUpload:
    async def test_creates_pending_learning_document_after_successful_upload(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Triggers doc generation",
                "upload_method": "paste",
                "paste_content": "print('hi')\n",
                "paste_filename": "main.py",
            },
        )
        assert response.status_code == 201
        task_id = uuid.UUID(response.json()["id"])

        result = await db_session.execute(
            select(LearningDocument).where(LearningDocument.task_id == task_id)
        )
        document = result.scalar_one()
        assert document.generation_status == "pending"
        assert set(document.content.keys()) == set(CHAPTER_KEYS)
        assert document.celery_task_id is not None

    async def test_does_not_create_document_when_upload_validation_fails(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Bad upload here", "upload_method": "file"},
            files=[("files", ("archive.zip", b"PK\x03\x04", "application/zip"))],
        )
        assert response.status_code == 400

        result = await db_session.execute(select(LearningDocument))
        assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# T097: GET /api/v1/tasks/{task_id}/document
# ---------------------------------------------------------------------------


class TestGetDocumentEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        task = await _make_task_without_upload(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 401

    async def test_returns_404_task_not_found_for_unknown_task(
        self, client, db_session
    ):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/document")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_404_task_not_found_for_other_users_task(
        self, client, db_session
    ):
        owner = await register_via_service(db_session)
        task = await _make_task_without_upload(db_session, owner)
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_404_learning_document_not_found_when_no_row(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Learning document not found"

    async def test_returns_pending_status_with_null_content_and_error(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        await _insert_document(db_session, task.id, generation_status="pending")

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "task_id": str(task.id),
            "status": "pending",
            "content": None,
            "error": None,
            "generated_at": None,
        }

    async def test_returns_completed_document_with_content_and_generated_at(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        completed_at = datetime.now(UTC)
        await _insert_document(
            db_session,
            task.id,
            content=VALID_DOCUMENT,
            generation_status="completed",
            generation_completed_at=completed_at,
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["content"] == VALID_DOCUMENT
        assert body["error"] is None
        assert body["generated_at"] == completed_at.isoformat()

    async def test_returns_failed_status_with_error_and_null_content(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        await _insert_document(
            db_session,
            task.id,
            generation_status="failed",
            generation_error="Gemini exploded",
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["content"] is None
        assert body["error"] == "Gemini exploded"


# ---------------------------------------------------------------------------
# T098: GET /api/v1/tasks/{task_id}/document/status
# ---------------------------------------------------------------------------


class TestGetDocumentStatusEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        task = await _make_task_without_upload(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 401

    async def test_returns_404_task_not_found_for_unknown_task(
        self, client, db_session
    ):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/document/status")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_404_learning_document_not_found_when_no_row(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Learning document not found"

    async def test_pending_status_has_null_estimated_seconds_remaining(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        await _insert_document(db_session, task.id, generation_status="pending")

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending"
        assert body["error"] is None
        assert body["estimated_seconds_remaining"] is None

    async def test_in_progress_status_estimates_remaining_seconds(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        started_at = datetime.now(UTC) - timedelta(seconds=30)
        await _insert_document(
            db_session,
            task.id,
            generation_status="in_progress",
            generation_started_at=started_at,
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "in_progress"
        remaining = body["estimated_seconds_remaining"]
        assert remaining is not None
        assert 140 <= remaining <= 155

    async def test_in_progress_estimate_never_goes_below_zero(self, client, db_session):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        started_at = datetime.now(UTC) - timedelta(seconds=10_000)
        await _insert_document(
            db_session,
            task.id,
            generation_status="in_progress",
            generation_started_at=started_at,
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        assert response.json()["estimated_seconds_remaining"] == 0

    async def test_completed_status_has_null_estimated_seconds_remaining(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        await _insert_document(
            db_session,
            task.id,
            content=VALID_DOCUMENT,
            generation_status="completed",
            generation_completed_at=datetime.now(UTC),
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["estimated_seconds_remaining"] is None

    async def test_failed_status_reports_error_and_null_estimate(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task_without_upload(db_session, user)
        await _insert_document(
            db_session,
            task.id,
            generation_status="failed",
            generation_error="Gemini exploded",
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/document/status")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "failed"
        assert body["error"] == "Gemini exploded"
        assert body["estimated_seconds_remaining"] is None
