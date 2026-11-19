"""Integration tests for the Tasks & Code Upload slice.

Covers tasks:
- T067 file_storage.save_file/read_file -> tests/unit/test_file_storage.py
- T068 TaskService (create/get/list/update/soft delete)
  -> src/services/task_service.py
- T069 CodeUploadService (validate/persist uploads)
  -> src/services/code_analysis/code_upload_service.py
- T070 GET    /api/v1/projects/{project_id}/tasks
- T071 POST   /api/v1/projects/{project_id}/tasks (multipart upload)
- T072 GET    /api/v1/tasks/{task_id}
- T073 PATCH  /api/v1/tasks/{task_id}
- T074 DELETE /api/v1/tasks/{task_id} (soft delete)
- T075 GET    /api/v1/tasks/{task_id}/code
"""

import uuid
from datetime import timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select

from src.db.session import get_db
from src.main import app
from src.models.task import Task
from src.services.auth.token_service import TokenService
from src.services.auth.user_service import UserService
from src.services.project_service import ProjectService

ACCESS_TOKEN_COOKIE_NAME = "access_token"
STRONG_PASSWORD = "Password123"


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


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


async def register_via_service(
    db_session, email: str | None = None, password: str = STRONG_PASSWORD
):
    return await UserService(db_session).register(
        email=email or unique_email(), password=password
    )


async def issue_tokens(db_session, user_id):
    return await TokenService(db_session).issue_tokens(user_id)


async def authenticated_client(client, db_session, email: str | None = None):
    user = await register_via_service(db_session, email=email)
    pair = await issue_tokens(db_session, user.id)
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
    return user


async def create_project(db_session, user_id, title: str = "Test project"):
    return await ProjectService(db_session).create(user_id=user_id, title=title)


# ---------------------------------------------------------------------------
# T068: TaskService
# ---------------------------------------------------------------------------


class TestTaskServiceCreate:
    async def test_create_persists_task_with_task_number_one(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)

        task = await TaskService(db_session).create(
            user_id=user.id,
            project_id=project.id,
            title="My first task",
            description="notes",
            upload_method="paste",
        )

        assert task.id is not None
        assert task.project_id == project.id
        assert task.task_number == 1
        assert task.title == "My first task"
        assert task.description == "notes"
        assert task.upload_method == "paste"
        assert task.deletion_status == "active"

    async def test_create_increments_task_number_per_project(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)

        first = await service.create(
            user_id=user.id, project_id=project.id, title="First task"
        )
        second = await service.create(
            user_id=user.id, project_id=project.id, title="Second task"
        )

        assert first.task_number == 1
        assert second.task_number == 2

    async def test_create_numbers_are_independent_per_project(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project_a = await create_project(db_session, user.id, title="Project A")
        project_b = await create_project(db_session, user.id, title="Project B")
        service = TaskService(db_session)

        await service.create(user_id=user.id, project_id=project_a.id, title="A task")
        task_b = await service.create(
            user_id=user.id, project_id=project_b.id, title="B task"
        )

        assert task_b.task_number == 1

    async def test_create_rejects_title_shorter_than_five_characters(self, db_session):
        from src.services.task_service import InvalidTaskTitleError, TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)

        with pytest.raises(InvalidTaskTitleError):
            await TaskService(db_session).create(
                user_id=user.id, project_id=project.id, title="Hi"
            )

    async def test_create_rejects_description_over_500_chars(self, db_session):
        from src.services.task_service import InvalidTaskDescriptionError, TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)

        with pytest.raises(InvalidTaskDescriptionError):
            await TaskService(db_session).create(
                user_id=user.id,
                project_id=project.id,
                title="Valid title",
                description="a" * 501,
            )

    async def test_create_raises_not_found_for_foreign_project(self, db_session):
        from src.services.project_service import ProjectNotFoundError
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)

        with pytest.raises(ProjectNotFoundError):
            await TaskService(db_session).create(
                user_id=intruder.id, project_id=project.id, title="Hijack attempt"
            )

    async def test_create_raises_not_found_for_trashed_project(self, db_session):
        from src.services.project_service import ProjectNotFoundError, ProjectService
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        await ProjectService(db_session).soft_delete(
            user_id=user.id, project_id=project.id
        )

        with pytest.raises(ProjectNotFoundError):
            await TaskService(db_session).create(
                user_id=user.id, project_id=project.id, title="Too late"
            )


class TestTaskServiceGet:
    async def test_get_returns_own_active_task(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        created = await service.create(
            user_id=user.id, project_id=project.id, title="Mine indeed"
        )

        fetched = await service.get(user_id=user.id, task_id=created.id)

        assert fetched.id == created.id

    async def test_get_returns_own_trashed_task(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Will be trashed"
        )
        await service.soft_delete(user_id=user.id, task_id=task.id)

        fetched = await service.get(user_id=user.id, task_id=task.id)

        assert fetched.deletion_status == "trashed"

    async def test_get_raises_not_found_for_unknown_id(self, db_session):
        from src.services.task_service import TaskNotFoundError, TaskService

        user = await register_via_service(db_session)

        with pytest.raises(TaskNotFoundError):
            await TaskService(db_session).get(user_id=user.id, task_id=uuid.uuid4())

    async def test_get_raises_not_found_for_other_users_task(self, db_session):
        from src.services.task_service import TaskNotFoundError, TaskService

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=owner.id, project_id=project.id, title="Owner's task"
        )

        with pytest.raises(TaskNotFoundError):
            await service.get(user_id=intruder.id, task_id=task.id)


class TestTaskServiceList:
    async def test_list_active_orders_by_task_number_ascending(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        await service.create(user_id=user.id, project_id=project.id, title="Task one")
        await service.create(user_id=user.id, project_id=project.id, title="Task two")
        await service.create(
            user_id=user.id, project_id=project.id, title="Task three"
        )

        tasks = await service.list_active(user_id=user.id, project_id=project.id)

        assert [t.task_number for t in tasks] == [1, 2, 3]

    async def test_list_active_excludes_trashed_tasks(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        keep = await service.create(
            user_id=user.id, project_id=project.id, title="Keep this one"
        )
        trash = await service.create(
            user_id=user.id, project_id=project.id, title="Trash this one"
        )
        await service.soft_delete(user_id=user.id, task_id=trash.id)

        tasks = await service.list_active(user_id=user.id, project_id=project.id)

        assert [t.id for t in tasks] == [keep.id]

    async def test_list_active_raises_not_found_for_foreign_project(self, db_session):
        from src.services.project_service import ProjectNotFoundError
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)

        with pytest.raises(ProjectNotFoundError):
            await TaskService(db_session).list_active(
                user_id=intruder.id, project_id=project.id
            )


class TestTaskServiceUpdate:
    async def test_update_changes_title_and_description(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id,
            project_id=project.id,
            title="Old title",
            description="Old description",
        )

        updated = await service.update(
            user_id=user.id,
            task_id=task.id,
            title="New title",
            description="New description",
        )

        assert updated.title == "New title"
        assert updated.description == "New description"

    async def test_update_without_title_leaves_title_unchanged(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Keep me"
        )

        updated = await service.update(
            user_id=user.id, task_id=task.id, description="Only description"
        )

        assert updated.title == "Keep me"
        assert updated.description == "Only description"

    async def test_update_raises_not_found_for_trashed_task(self, db_session):
        from src.services.task_service import TaskNotFoundError, TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Will be trashed"
        )
        await service.soft_delete(user_id=user.id, task_id=task.id)

        with pytest.raises(TaskNotFoundError):
            await service.update(user_id=user.id, task_id=task.id, title="Too late")


class TestTaskServiceSoftDelete:
    async def test_soft_delete_marks_trashed_with_30_day_retention(self, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="To be trashed"
        )

        deleted = await service.soft_delete(user_id=user.id, task_id=task.id)

        assert deleted.deletion_status == "trashed"
        assert deleted.trashed_at is not None
        assert deleted.scheduled_deletion_at - deleted.trashed_at == timedelta(days=30)

        result = await db_session.execute(select(Task).where(Task.id == task.id))
        assert result.scalar_one().deletion_status == "trashed"

    async def test_soft_delete_raises_not_found_for_already_trashed_task(
        self, db_session
    ):
        from src.services.task_service import TaskNotFoundError, TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Trash me twice"
        )
        await service.soft_delete(user_id=user.id, task_id=task.id)

        with pytest.raises(TaskNotFoundError):
            await service.soft_delete(user_id=user.id, task_id=task.id)


# ---------------------------------------------------------------------------
# T069: CodeUploadService.create_upload / get_for_task
# ---------------------------------------------------------------------------


class TestCodeUploadServiceCreateUpload:
    async def test_create_upload_detects_language_and_complexity(self, db_session):
        from src.services.code_analysis.code_upload_service import (
            CodeUploadService,
            UploadedFileInput,
        )
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Upload target"
        )

        result = await CodeUploadService(db_session).create_upload(
            user_id=user.id,
            task_id=task.id,
            files=[UploadedFileInput(filename="main.py", content=b"print(1)\n")],
        )

        assert result.uploaded_code.detected_language == "python"
        assert result.uploaded_code.complexity_level == "beginner"
        assert result.uploaded_code.total_lines == 1
        assert result.uploaded_code.total_files == 1
        assert result.uploaded_code.upload_size_bytes == len(b"print(1)\n")
        assert len(result.files) == 1
        assert result.files[0].file_name == "main.py"

    async def test_create_upload_falls_back_to_none_language_for_text_only(
        self, db_session
    ):
        from src.services.code_analysis.code_upload_service import (
            CodeUploadService,
            UploadedFileInput,
        )
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Text only upload"
        )

        result = await CodeUploadService(db_session).create_upload(
            user_id=user.id,
            task_id=task.id,
            files=[UploadedFileInput(filename="notes.txt", content=b"just notes")],
        )

        assert result.uploaded_code.detected_language is None

    async def test_create_upload_persists_readable_file_content(self, db_session):
        from src.services.code_analysis import file_storage
        from src.services.code_analysis.code_upload_service import (
            CodeUploadService,
            UploadedFileInput,
        )
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Persist target"
        )

        result = await CodeUploadService(db_session).create_upload(
            user_id=user.id,
            task_id=task.id,
            files=[UploadedFileInput(filename="src/app.py", content=b"x = 1\n")],
        )

        code_file = result.files[0]
        assert code_file.file_path == "src/app.py"
        assert code_file.file_name == "app.py"
        assert file_storage.read_file(code_file.storage_path) == b"x = 1\n"

    async def test_get_for_task_returns_none_without_upload(self, db_session):
        from src.services.code_analysis.code_upload_service import CodeUploadService
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="No upload yet"
        )

        result = await CodeUploadService(db_session).get_for_task(task.id)

        assert result is None


# ---------------------------------------------------------------------------
# T070: GET /api/v1/projects/{project_id}/tasks
# ---------------------------------------------------------------------------


class TestListTasksEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)

        response = await client.get(f"/api/v1/projects/{project.id}/tasks")

        assert response.status_code == 401

    async def test_returns_active_tasks_ordered_by_task_number(
        self, client, db_session
    ):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        await service.create(user_id=user.id, project_id=project.id, title="Task one")
        second = await service.create(
            user_id=user.id, project_id=project.id, title="Task two"
        )
        await service.create(user_id=user.id, project_id=project.id, title="Task 3rd")
        await service.soft_delete(user_id=user.id, task_id=second.id)

        response = await client.get(f"/api/v1/projects/{project.id}/tasks")

        assert response.status_code == 200
        body = response.json()
        assert [t["task_number"] for t in body] == [1, 3]

    async def test_returns_404_for_foreign_project(self, client, db_session):
        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/projects/{project.id}/tasks")

        assert response.status_code == 404

    async def test_returns_404_for_trashed_project(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        await ProjectService(db_session).soft_delete(
            user_id=user.id, project_id=project.id
        )

        response = await client.get(f"/api/v1/projects/{project.id}/tasks")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# T071: POST /api/v1/projects/{project_id}/tasks
# ---------------------------------------------------------------------------


class TestCreateTaskEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Needs auth",
                "upload_method": "paste",
                "paste_content": "print(1)",
                "paste_filename": "main.py",
            },
        )

        assert response.status_code == 401

    async def test_creates_task_via_paste_upload(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Paste upload task",
                "description": "via paste",
                "upload_method": "paste",
                "paste_content": "print('hello')\n",
                "paste_filename": "solution.py",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Paste upload task"
        assert body["description"] == "via paste"
        assert body["upload_method"] == "paste"
        assert body["task_number"] == 1
        assert body["deletion_status"] == "active"
        uploaded = body["uploaded_code"]
        assert uploaded["detected_language"] == "python"
        assert uploaded["total_files"] == 1
        assert uploaded["files"][0]["file_name"] == "solution.py"

    async def test_creates_task_via_single_file_upload(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "File upload task", "upload_method": "file"},
            files=[("files", ("main.py", b"print(1)\n", "text/plain"))],
        )

        assert response.status_code == 201
        body = response.json()
        assert body["uploaded_code"]["total_files"] == 1
        assert body["uploaded_code"]["files"][0]["file_path"] is None

    async def test_creates_task_via_folder_upload_preserving_relative_paths(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Folder upload task", "upload_method": "folder"},
            files=[
                ("files", ("main.py", b"print(1)\n", "text/plain")),
                ("files", ("src/app.py", b"print(2)\n", "text/plain")),
                ("files", (".git/config", b"binarygitstuff", "text/plain")),
            ],
        )

        assert response.status_code == 201
        body = response.json()
        file_paths = {f["file_path"] for f in body["uploaded_code"]["files"]}
        assert file_paths == {None, "src/app.py"}
        assert body["uploaded_code"]["total_files"] == 2

    async def test_rejects_title_shorter_than_five_characters(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Hi",
                "upload_method": "paste",
                "paste_content": "print(1)",
                "paste_filename": "main.py",
            },
        )

        assert response.status_code == 400
        assert "message" in response.json()["error"]

    async def test_rejects_description_over_500_chars(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Valid title here",
                "description": "a" * 501,
                "upload_method": "paste",
                "paste_content": "print(1)",
                "paste_filename": "main.py",
            },
        )

        assert response.status_code == 400

    async def test_rejects_invalid_upload_method(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "carrier-pigeon"},
        )

        assert response.status_code == 400

    async def test_rejects_paste_without_paste_content(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Valid title here",
                "upload_method": "paste",
                "paste_filename": "main.py",
            },
        )

        assert response.status_code == 400

    async def test_rejects_file_upload_without_files(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "file"},
        )

        assert response.status_code == 400

    async def test_rejects_path_traversal_in_filename(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "folder"},
            files=[("files", ("../../etc/passwd", b"evil", "text/plain"))],
        )

        assert response.status_code == 400

    async def test_rejects_more_than_twenty_files(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        upload_files = [
            ("files", (f"file{i}.py", b"print(1)\n", "text/plain")) for i in range(21)
        ]

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "folder"},
            files=upload_files,
        )

        assert response.status_code == 400

    async def test_rejects_unsupported_file_extension(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "file"},
            files=[("files", ("archive.zip", b"PK\x03\x04", "application/zip"))],
        )

        assert response.status_code == 400

    async def test_rejects_binary_file_content(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "file"},
            files=[("files", ("image.py", b"\x89PNG\x00\x01\x02", "text/plain"))],
        )

        assert response.status_code == 400

    async def test_does_not_persist_orphan_task_when_validation_fails(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={"title": "Valid title here", "upload_method": "file"},
            files=[("files", ("archive.zip", b"PK\x03\x04", "application/zip"))],
        )
        assert response.status_code == 400

        result = await db_session.execute(
            select(Task).where(Task.project_id == project.id)
        )
        assert result.scalars().all() == []

    async def test_returns_404_for_foreign_project(self, client, db_session):
        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        await authenticated_client(client, db_session)

        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Hijack attempt",
                "upload_method": "paste",
                "paste_content": "print(1)",
                "paste_filename": "main.py",
            },
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# T072: GET /api/v1/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestGetTaskEndpoint:
    async def test_requires_authentication(self, client, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Someone's task"
        )

        response = await client.get(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 401

    async def test_returns_own_task(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id,
            project_id=project.id,
            title="My task",
            description="Details",
        )

        response = await client.get(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(task.id)
        assert body["title"] == "My task"
        assert body["uploaded_code"] is None

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_returns_404_for_other_users_task(self, client, db_session):
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        task = await TaskService(db_session).create(
            user_id=owner.id, project_id=project.id, title="Owner's task"
        )
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# T073: PATCH /api/v1/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestUpdateTaskEndpoint:
    async def test_updates_own_task(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Old title"
        )

        response = await client.patch(
            f"/api/v1/tasks/{task.id}", json={"title": "New valid title"}
        )

        assert response.status_code == 200
        assert response.json()["title"] == "New valid title"

    async def test_rejects_title_shorter_than_five_characters(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Valid title"
        )

        response = await client.patch(f"/api/v1/tasks/{task.id}", json={"title": "Hi"})

        assert response.status_code == 400

    async def test_returns_404_for_trashed_task(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Will be trashed"
        )
        await service.soft_delete(user_id=user.id, task_id=task.id)

        response = await client.patch(
            f"/api/v1/tasks/{task.id}", json={"title": "Cannot edit this"}
        )

        assert response.status_code == 404

    async def test_returns_404_for_other_users_task(self, client, db_session):
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        task = await TaskService(db_session).create(
            user_id=owner.id, project_id=project.id, title="Owner's task"
        )
        await authenticated_client(client, db_session)

        response = await client.patch(
            f"/api/v1/tasks/{task.id}", json={"title": "Hijacked title"}
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# T074: DELETE /api/v1/tasks/{task_id}
# ---------------------------------------------------------------------------


class TestDeleteTaskEndpoint:
    async def test_soft_deletes_own_task(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="To delete"
        )

        response = await client.delete(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["deletion_status"] == "trashed"

        result = await db_session.execute(select(Task).where(Task.id == task.id))
        still_in_db = result.scalar_one()
        assert still_in_db.deletion_status == "trashed"
        assert still_in_db.trashed_at is not None

    async def test_returns_404_for_already_trashed_task(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        service = TaskService(db_session)
        task = await service.create(
            user_id=user.id, project_id=project.id, title="Trash me twice"
        )
        await service.soft_delete(user_id=user.id, task_id=task.id)

        response = await client.delete(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 404

    async def test_returns_404_for_other_users_task(self, client, db_session):
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        task = await TaskService(db_session).create(
            user_id=owner.id, project_id=project.id, title="Owner's task"
        )
        await authenticated_client(client, db_session)

        response = await client.delete(f"/api/v1/tasks/{task.id}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# T075: GET /api/v1/tasks/{task_id}/code
# ---------------------------------------------------------------------------


class TestGetTaskCodeEndpoint:
    async def test_returns_file_contents_for_own_task(self, client, db_session):
        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)

        create_response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            data={
                "title": "Code retrieval task",
                "upload_method": "paste",
                "paste_content": "print('hi')\n",
                "paste_filename": "main.py",
            },
        )
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/tasks/{task_id}/code")

        assert response.status_code == 200
        body = response.json()
        assert body["files"] == [
            {
                "file_name": "main.py",
                "file_path": None,
                "file_extension": ".py",
                "content": "print('hi')\n",
            }
        ]

    async def test_returns_empty_files_when_no_upload_exists(self, client, db_session):
        from src.services.task_service import TaskService

        user = await authenticated_client(client, db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="No upload yet"
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/code")

        assert response.status_code == 200
        assert response.json() == {"files": []}

    async def test_returns_404_for_other_users_task(self, client, db_session):
        from src.services.task_service import TaskService

        owner = await register_via_service(db_session)
        project = await create_project(db_session, owner.id)
        task = await TaskService(db_session).create(
            user_id=owner.id, project_id=project.id, title="Owner's task"
        )
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{task.id}/code")

        assert response.status_code == 404

    async def test_requires_authentication(self, client, db_session):
        from src.services.task_service import TaskService

        user = await register_via_service(db_session)
        project = await create_project(db_session, user.id)
        task = await TaskService(db_session).create(
            user_id=user.id, project_id=project.id, title="Someone's task"
        )

        response = await client.get(f"/api/v1/tasks/{task.id}/code")

        assert response.status_code == 401
