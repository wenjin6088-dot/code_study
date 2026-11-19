"""Integration tests for the Projects slice (RED phase).

Covers tasks:
- T043 Project SQLAlchemy model              -> src/models/project.py
- T044 ProjectService (create/get/list/update/soft delete)
                                              -> src/services/project_service.py
- T045 Project ownership validation (ProjectService)
- T046 GET    /api/v1/projects
- T047 POST   /api/v1/projects
- T048 GET    /api/v1/projects/{project_id}
- T049 PATCH  /api/v1/projects/{project_id}
- T050 DELETE /api/v1/projects/{project_id}  (soft delete)

None of src/models/project.py, src/services/project_service.py or
src/api/projects.py exist yet, and the projects router is not registered on
api_router. Every test below is therefore expected to FAIL until the GREEN
phase implements them -- most as a ModuleNotFoundError/ImportError raised at
the point a test imports Project/ProjectService, and the pure-HTTP endpoint
tests (ones that never import those modules directly, e.g. the 401 checks)
as AssertionErrors because /api/v1/projects doesn't exist yet and the app
currently returns 404 for every method on that unregistered path.

Contract encoded here for the implementer:

ProjectService(session) exposes:
    - create(user_id, title, description=None) -> Project
    - get(user_id, project_id) -> Project
        Any deletion_status (active or trashed) is returned as long as the
        caller owns it. Raises ProjectNotFoundError if the id doesn't exist
        OR belongs to a different user -- a wrong owner must look identical
        to "doesn't exist" (no existence leakage via a 403).
    - list_active(user_id) -> list[Project]
        Only the caller's projects with deletion_status == 'active'.
    - update(user_id, project_id, title=None, description=None) -> Project
        Only ACTIVE, owned projects may be updated (a trashed project raises
        ProjectNotFoundError, same as a missing/foreign one). `None` means
        "leave this field unchanged" (so you cannot blank out description
        via this call).
    - soft_delete(user_id, project_id) -> Project
        Only ACTIVE, owned projects may be deleted (deleting an
        already-trashed/missing/foreign project raises ProjectNotFoundError).
        Sets deletion_status='trashed', trashed_at=now,
        scheduled_deletion_at=trashed_at + timedelta(days=30). The row is
        NEVER removed from the database.

and raises:
    - ProjectNotFoundError     (missing / not owned / not active where required)
    - InvalidProjectTitleError (empty or whitespace-only title)

API endpoints (prefix /api/v1/projects, authenticated via the same
"access_token" httponly cookie as /api/v1/auth/*, through the existing
get_current_user dependency):
    - GET    /api/v1/projects      -> 200, JSON array of the caller's ACTIVE projects
    - POST   /api/v1/projects      -> 201, body {"title": str, "description"?: str}
    - GET    /api/v1/projects/{id} -> 200 / 404
    - PATCH  /api/v1/projects/{id} -> 200 / 404 / 400
    - DELETE /api/v1/projects/{id} -> 200 with the now-trashed project body / 404

Every project JSON object includes at least "id", "title", "description",
"deletion_status". ProjectNotFoundError -> 404, InvalidProjectTitleError ->
400 (AppException), missing/invalid auth cookie -> 401, matching the
existing {"error": {"message": ...}} envelope.
"""

import uuid
from datetime import timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.db.session import get_db
from src.main import app
from src.services.auth.token_service import TokenService
from src.services.auth.user_service import UserService

ACCESS_TOKEN_COOKIE_NAME = "access_token"
STRONG_PASSWORD = "Password123"


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(autouse=True)
def _jwt_secrets(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")


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
    """Register a fresh user, issue tokens, and set the access-token cookie.

    Returns the created User so callers can create projects owned by them.
    """
    user = await register_via_service(db_session, email=email)
    pair = await issue_tokens(db_session, user.id)
    client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
    return user


# ---------------------------------------------------------------------------
# T043: Project model
# ---------------------------------------------------------------------------


class TestProjectModel:
    async def test_create_project_applies_defaults(self, db_session):
        from src.models.project import Project

        user = await register_via_service(db_session)
        project = Project(user_id=user.id, title="My First Project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.id is not None
        assert project.user_id == user.id
        assert project.title == "My First Project"
        assert project.description is None
        assert project.deletion_status == "active"
        assert project.trashed_at is None
        assert project.scheduled_deletion_at is None
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.last_activity_at is not None

    async def test_empty_title_violates_title_min_length_check(self, db_session):
        from src.models.project import Project

        user = await register_via_service(db_session)
        project = Project(user_id=user.id, title="")
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    async def test_project_requires_user_id(self, db_session):
        from src.models.project import Project

        project = Project(title="Orphan project")
        db_session.add(project)

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()


# ---------------------------------------------------------------------------
# T044/T045: ProjectService
# ---------------------------------------------------------------------------


class TestProjectServiceCreate:
    async def test_create_persists_project_owned_by_user(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Learn FastAPI", description="notes"
        )

        assert project.id is not None
        assert project.user_id == user.id
        assert project.title == "Learn FastAPI"
        assert project.description == "notes"
        assert project.deletion_status == "active"

    async def test_create_allows_omitted_description(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="No description project"
        )

        assert project.description is None

    async def test_create_rejects_empty_title(self, db_session):
        from src.services.project_service import (
            InvalidProjectTitleError,
            ProjectService,
        )

        user = await register_via_service(db_session)

        with pytest.raises(InvalidProjectTitleError):
            await ProjectService(db_session).create(user_id=user.id, title="")

    async def test_create_rejects_whitespace_only_title(self, db_session):
        from src.services.project_service import (
            InvalidProjectTitleError,
            ProjectService,
        )

        user = await register_via_service(db_session)

        with pytest.raises(InvalidProjectTitleError):
            await ProjectService(db_session).create(user_id=user.id, title="   ")


class TestProjectServiceGet:
    async def test_get_returns_own_project(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        created = await service.create(user_id=user.id, title="Mine")

        fetched = await service.get(user_id=user.id, project_id=created.id)

        assert fetched.id == created.id

    async def test_get_returns_trashed_project_owned_by_caller(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Will be trashed")
        await service.soft_delete(user_id=user.id, project_id=project.id)

        fetched = await service.get(user_id=user.id, project_id=project.id)

        assert fetched.id == project.id
        assert fetched.deletion_status == "trashed"

    async def test_get_raises_not_found_for_unknown_id(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        user = await register_via_service(db_session)

        with pytest.raises(ProjectNotFoundError):
            await ProjectService(db_session).get(
                user_id=user.id, project_id=uuid.uuid4()
            )

    async def test_get_raises_not_found_for_other_users_project(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=owner.id, title="Owner's project")

        with pytest.raises(ProjectNotFoundError):
            await service.get(user_id=intruder.id, project_id=project.id)


class TestProjectServiceList:
    async def test_list_active_returns_only_callers_active_projects(self, db_session):
        from src.services.project_service import ProjectService

        owner = await register_via_service(db_session)
        other = await register_via_service(db_session)
        service = ProjectService(db_session)
        active = await service.create(user_id=owner.id, title="Active project")
        trashed = await service.create(user_id=owner.id, title="Trashed project")
        await service.soft_delete(user_id=owner.id, project_id=trashed.id)
        await service.create(user_id=other.id, title="Someone else's project")

        projects = await service.list_active(user_id=owner.id)

        ids = {p.id for p in projects}
        assert ids == {active.id}

    async def test_list_active_returns_empty_list_for_user_with_no_projects(
        self, db_session
    ):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)

        projects = await ProjectService(db_session).list_active(user_id=user.id)

        assert projects == []


class TestProjectServiceUpdate:
    async def test_update_changes_title_and_description(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(
            user_id=user.id, title="Old title", description="Old description"
        )

        updated = await service.update(
            user_id=user.id,
            project_id=project.id,
            title="New title",
            description="New description",
        )

        assert updated.title == "New title"
        assert updated.description == "New description"

    async def test_update_without_title_leaves_title_unchanged(self, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Keep me")

        updated = await service.update(
            user_id=user.id, project_id=project.id, description="Only description"
        )

        assert updated.title == "Keep me"
        assert updated.description == "Only description"

    async def test_update_rejects_empty_title(self, db_session):
        from src.services.project_service import (
            InvalidProjectTitleError,
            ProjectService,
        )

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Valid title")

        with pytest.raises(InvalidProjectTitleError):
            await service.update(user_id=user.id, project_id=project.id, title="")

    async def test_update_raises_not_found_for_unknown_id(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        user = await register_via_service(db_session)

        with pytest.raises(ProjectNotFoundError):
            await ProjectService(db_session).update(
                user_id=user.id, project_id=uuid.uuid4(), title="Nope"
            )

    async def test_update_raises_not_found_for_other_users_project(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=owner.id, title="Owner's project")

        with pytest.raises(ProjectNotFoundError):
            await service.update(
                user_id=intruder.id, project_id=project.id, title="Hijacked"
            )

    async def test_update_raises_not_found_for_trashed_project(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Will be trashed")
        await service.soft_delete(user_id=user.id, project_id=project.id)

        with pytest.raises(ProjectNotFoundError):
            await service.update(
                user_id=user.id, project_id=project.id, title="Cannot edit"
            )


class TestProjectServiceSoftDelete:
    async def test_soft_delete_marks_trashed_without_removing_row(self, db_session):
        from src.models.project import Project
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="To be trashed")

        deleted = await service.soft_delete(user_id=user.id, project_id=project.id)

        assert deleted.deletion_status == "trashed"
        assert deleted.trashed_at is not None
        assert deleted.scheduled_deletion_at is not None
        assert deleted.scheduled_deletion_at - deleted.trashed_at == timedelta(days=30)

        result = await db_session.execute(
            select(Project).where(Project.id == project.id)
        )
        still_in_db = result.scalar_one()
        assert still_in_db.deletion_status == "trashed"
        assert still_in_db.trashed_at is not None

    async def test_soft_delete_raises_not_found_for_other_users_project(
        self, db_session
    ):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        owner = await register_via_service(db_session)
        intruder = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=owner.id, title="Owner's project")

        with pytest.raises(ProjectNotFoundError):
            await service.soft_delete(user_id=intruder.id, project_id=project.id)

    async def test_soft_delete_raises_not_found_for_unknown_id(self, db_session):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        user = await register_via_service(db_session)

        with pytest.raises(ProjectNotFoundError):
            await ProjectService(db_session).soft_delete(
                user_id=user.id, project_id=uuid.uuid4()
            )

    async def test_soft_delete_raises_not_found_for_already_trashed_project(
        self, db_session
    ):
        from src.services.project_service import (
            ProjectNotFoundError,
            ProjectService,
        )

        user = await register_via_service(db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Trash me twice")
        await service.soft_delete(user_id=user.id, project_id=project.id)

        with pytest.raises(ProjectNotFoundError):
            await service.soft_delete(user_id=user.id, project_id=project.id)


# ---------------------------------------------------------------------------
# T046-T050: /api/v1/projects endpoints
# ---------------------------------------------------------------------------


class TestListProjectsEndpoint:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/projects")

        assert response.status_code == 401

    async def test_rejects_garbage_token_with_401(self, client):
        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "garbage-token")
        response = await client.get("/api/v1/projects")

        assert response.status_code == 401

    async def test_returns_only_callers_active_projects(self, client, db_session):
        from src.services.project_service import ProjectService

        owner = await authenticated_client(client, db_session)
        service = ProjectService(db_session)
        active = await service.create(user_id=owner.id, title="Active project")
        trashed = await service.create(user_id=owner.id, title="Trashed project")
        await service.soft_delete(user_id=owner.id, project_id=trashed.id)

        other = await register_via_service(db_session)
        await service.create(user_id=other.id, title="Not mine")

        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        body = response.json()
        ids = {item["id"] for item in body}
        assert ids == {str(active.id)}

    async def test_returns_empty_array_for_user_with_no_projects(
        self, client, db_session
    ):
        await authenticated_client(client, db_session)

        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        assert response.json() == []


class TestCreateProjectEndpoint:
    async def test_requires_authentication(self, client):
        response = await client.post(
            "/api/v1/projects", json={"title": "New project"}
        )

        assert response.status_code == 401

    async def test_creates_project_for_authenticated_user(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post(
            "/api/v1/projects",
            json={"title": "Learn SQL", "description": "Practice joins"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Learn SQL"
        assert body["description"] == "Practice joins"
        assert body["deletion_status"] == "active"
        assert "id" in body

    async def test_creates_project_without_description(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post(
            "/api/v1/projects", json={"title": "No description"}
        )

        assert response.status_code == 201
        assert response.json()["description"] is None

    async def test_rejects_missing_title_with_422(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post("/api/v1/projects", json={})

        assert response.status_code == 422

    async def test_rejects_empty_title_with_400(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post("/api/v1/projects", json={"title": ""})

        assert response.status_code == 400
        assert "message" in response.json()["error"]

    async def test_rejects_whitespace_only_title_with_400(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post("/api/v1/projects", json={"title": "   "})

        assert response.status_code == 400


class TestGetProjectEndpoint:
    async def test_requires_authentication(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Someone's project"
        )

        response = await client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 401

    async def test_returns_own_project(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="My project", description="Details"
        )

        response = await client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(project.id)
        assert body["title"] == "My project"
        assert body["description"] == "Details"

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/projects/{uuid.uuid4()}")

        assert response.status_code == 404
        assert "message" in response.json()["error"]

    async def test_returns_404_for_other_users_project(self, client, db_session):
        from src.services.project_service import ProjectService

        owner = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=owner.id, title="Owner's project"
        )
        await authenticated_client(client, db_session)  # a different, intruding user

        response = await client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 404

    async def test_returns_422_for_malformed_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.get("/api/v1/projects/not-a-uuid")

        assert response.status_code == 422


class TestUpdateProjectEndpoint:
    async def test_requires_authentication(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Someone's project"
        )

        response = await client.patch(
            f"/api/v1/projects/{project.id}", json={"title": "Hijacked"}
        )

        assert response.status_code == 401

    async def test_updates_own_project(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Old title", description="Old description"
        )

        response = await client.patch(
            f"/api/v1/projects/{project.id}",
            json={"title": "New title", "description": "New description"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "New title"
        assert body["description"] == "New description"

    async def test_updates_only_description_leaves_title_unchanged(
        self, client, db_session
    ):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Keep me"
        )

        response = await client.patch(
            f"/api/v1/projects/{project.id}",
            json={"description": "Only description changed"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Keep me"
        assert body["description"] == "Only description changed"

    async def test_returns_404_for_other_users_project(self, client, db_session):
        from src.services.project_service import ProjectService

        owner = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=owner.id, title="Owner's project"
        )
        await authenticated_client(client, db_session)

        response = await client.patch(
            f"/api/v1/projects/{project.id}", json={"title": "Hijacked"}
        )

        assert response.status_code == 404

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.patch(
            f"/api/v1/projects/{uuid.uuid4()}", json={"title": "Nope"}
        )

        assert response.status_code == 404

    async def test_rejects_empty_title_with_400(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Valid title"
        )

        response = await client.patch(
            f"/api/v1/projects/{project.id}", json={"title": ""}
        )

        assert response.status_code == 400

    async def test_returns_404_for_trashed_project(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Will be trashed")
        await service.soft_delete(user_id=user.id, project_id=project.id)

        response = await client.patch(
            f"/api/v1/projects/{project.id}", json={"title": "Cannot edit"}
        )

        assert response.status_code == 404


class TestDeleteProjectEndpoint:
    async def test_requires_authentication(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="Someone's project"
        )

        response = await client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 401

    async def test_soft_deletes_own_project(self, client, db_session):
        from src.models.project import Project
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="To delete"
        )

        response = await client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["deletion_status"] == "trashed"

        result = await db_session.execute(
            select(Project).where(Project.id == project.id)
        )
        still_in_db = result.scalar_one()
        assert still_in_db.deletion_status == "trashed"
        assert still_in_db.trashed_at is not None

    async def test_deleted_project_excluded_from_list(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        project = await ProjectService(db_session).create(
            user_id=user.id, title="To delete"
        )

        delete_response = await client.delete(f"/api/v1/projects/{project.id}")
        assert delete_response.status_code == 200

        list_response = await client.get("/api/v1/projects")

        assert list_response.status_code == 200
        ids = {item["id"] for item in list_response.json()}
        assert str(project.id) not in ids

    async def test_returns_404_for_other_users_project(self, client, db_session):
        from src.services.project_service import ProjectService

        owner = await register_via_service(db_session)
        project = await ProjectService(db_session).create(
            user_id=owner.id, title="Owner's project"
        )
        await authenticated_client(client, db_session)

        response = await client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 404

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.delete(f"/api/v1/projects/{uuid.uuid4()}")

        assert response.status_code == 404

    async def test_returns_404_for_already_trashed_project(self, client, db_session):
        from src.services.project_service import ProjectService

        user = await authenticated_client(client, db_session)
        service = ProjectService(db_session)
        project = await service.create(user_id=user.id, title="Trash me twice")
        await service.soft_delete(user_id=user.id, project_id=project.id)

        response = await client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == 404
