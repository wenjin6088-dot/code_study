"""Integration tests for the Trash slice (RED phase), projects only.

Task-trash (TrashedTaskCard, task restore/permanent-delete) is explicitly
OUT of scope here: the Task entity doesn't exist yet (Phase 5 is still all
`[ ]` in tasks.md), so there is nothing to restore/delete. Likewise the
30-day scheduled auto-delete Celery task (T172) is out of scope — this file
only covers the user-triggered restore/permanent-delete flow for projects.

Contract encoded here for the implementer:

TrashService(session) exposes:
    - list_trashed_projects(user_id) -> list[Project]
        Only the caller's projects with deletion_status == 'trashed'.
    - restore_project(user_id, project_id) -> Project
        Only a TRASHED, owned project may be restored (active/missing/
        foreign all raise ProjectNotFoundError, same "doesn't leak
        existence" rule as ProjectService). Sets deletion_status='active',
        trashed_at=None, scheduled_deletion_at=None.
    - permanent_delete_project(user_id, project_id) -> None
        Only a TRASHED, owned project may be permanently deleted (active/
        missing/foreign all raise ProjectNotFoundError). Row is actually
        removed from the database (hard delete) — this is irreversible,
        unlike ProjectService.soft_delete.

Reuses ProjectNotFoundError from src.services.project_service (same error
type as the rest of the Projects slice; the API layer already knows how to
map it to 404).

API endpoints (prefix /api/v1/trash, same cookie auth as /projects):
    - GET    /api/v1/trash
      -> 200, {"projects": [...]} (caller's trashed projects)
    - POST   /api/v1/trash/projects/{id}/restore
      -> 200 (now-active project) / 404
    - DELETE /api/v1/trash/projects/{id}/permanent-delete
      -> 204 / 404
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from src.db.session import get_db
from src.main import app
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


async def create_trashed_project(db_session, user_id, title="Trashed project"):
    svc = ProjectService(db_session)
    project = await svc.create(user_id=user_id, title=title)
    return await svc.soft_delete(user_id=user_id, project_id=project.id)


# ---------------------------------------------------------------------------
# TrashService.list_trashed_projects
# ---------------------------------------------------------------------------
class TestTrashServiceListTrashedProjects:
    async def test_returns_only_callers_trashed_projects(self, db_session):
        from src.services.trash_service import TrashService

        owner = await register_via_service(db_session)
        other = await register_via_service(db_session)

        trashed = await create_trashed_project(db_session, owner.id, "Mine (trashed)")
        await ProjectService(db_session).create(user_id=owner.id, title="Mine (active)")
        await create_trashed_project(db_session, other.id, "Theirs (trashed)")

        results = await TrashService(db_session).list_trashed_projects(user_id=owner.id)

        assert [p.id for p in results] == [trashed.id]

    async def test_returns_empty_list_when_nothing_trashed(self, db_session):
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)

        results = await TrashService(db_session).list_trashed_projects(user_id=user.id)

        assert results == []


# ---------------------------------------------------------------------------
# TrashService.restore_project
# ---------------------------------------------------------------------------
class TestTrashServiceRestoreProject:
    async def test_restore_reactivates_and_clears_trash_fields(self, db_session):
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, user.id)

        restored = await TrashService(db_session).restore_project(
            user_id=user.id, project_id=trashed.id
        )

        assert restored.deletion_status == "active"
        assert restored.trashed_at is None
        assert restored.scheduled_deletion_at is None

    async def test_restore_raises_not_found_for_active_project(self, db_session):
        from src.services.project_service import ProjectNotFoundError
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)
        active = await ProjectService(db_session).create(
            user_id=user.id, title="Active"
        )

        with pytest.raises(ProjectNotFoundError):
            await TrashService(db_session).restore_project(
                user_id=user.id, project_id=active.id
            )

    async def test_restore_raises_not_found_for_other_users_project(self, db_session):
        from src.services.project_service import ProjectNotFoundError
        from src.services.trash_service import TrashService

        owner = await register_via_service(db_session)
        other = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, owner.id)

        with pytest.raises(ProjectNotFoundError):
            await TrashService(db_session).restore_project(
                user_id=other.id, project_id=trashed.id
            )

    async def test_restore_raises_not_found_for_unknown_id(self, db_session):
        from src.services.project_service import ProjectNotFoundError
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)

        with pytest.raises(ProjectNotFoundError):
            await TrashService(db_session).restore_project(
                user_id=user.id, project_id=uuid.uuid4()
            )


# ---------------------------------------------------------------------------
# TrashService.permanent_delete_project
# ---------------------------------------------------------------------------
class TestTrashServicePermanentDeleteProject:
    async def test_permanent_delete_removes_row_from_database(self, db_session):
        from sqlalchemy import select

        from src.models.project import Project
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, user.id)

        await TrashService(db_session).permanent_delete_project(
            user_id=user.id, project_id=trashed.id
        )

        result = await db_session.execute(
            select(Project).where(Project.id == trashed.id)
        )
        assert result.scalar_one_or_none() is None

    async def test_permanent_delete_raises_not_found_for_active_project(
        self, db_session
    ):
        from src.services.project_service import ProjectNotFoundError
        from src.services.trash_service import TrashService

        user = await register_via_service(db_session)
        active = await ProjectService(db_session).create(
            user_id=user.id, title="Active"
        )

        with pytest.raises(ProjectNotFoundError):
            await TrashService(db_session).permanent_delete_project(
                user_id=user.id, project_id=active.id
            )

    async def test_permanent_delete_raises_not_found_for_other_users_project(
        self, db_session
    ):
        from src.services.project_service import ProjectNotFoundError
        from src.services.trash_service import TrashService

        owner = await register_via_service(db_session)
        other = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, owner.id)

        with pytest.raises(ProjectNotFoundError):
            await TrashService(db_session).permanent_delete_project(
                user_id=other.id, project_id=trashed.id
            )


# ---------------------------------------------------------------------------
# GET /api/v1/trash
# ---------------------------------------------------------------------------
class TestListTrashEndpoint:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/trash")

        assert response.status_code == 401

    async def test_returns_only_callers_trashed_projects(self, client, db_session):
        user = await authenticated_client(client, db_session)
        trashed = await create_trashed_project(db_session, user.id, "Trashed one")
        await ProjectService(db_session).create(user_id=user.id, title="Active one")

        response = await client.get("/api/v1/trash")

        assert response.status_code == 200
        body = response.json()
        assert [p["id"] for p in body["projects"]] == [str(trashed.id)]


# ---------------------------------------------------------------------------
# POST /api/v1/trash/projects/{id}/restore
# ---------------------------------------------------------------------------
class TestRestoreProjectEndpoint:
    async def test_requires_authentication(self, client):
        response = await client.post(f"/api/v1/trash/projects/{uuid.uuid4()}/restore")

        assert response.status_code == 401

    async def test_restores_own_trashed_project(self, client, db_session):
        user = await authenticated_client(client, db_session)
        trashed = await create_trashed_project(db_session, user.id)

        response = await client.post(f"/api/v1/trash/projects/{trashed.id}/restore")

        assert response.status_code == 200
        assert response.json()["deletion_status"] == "active"

    async def test_returns_404_for_other_users_project(self, client, db_session):
        owner = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, owner.id)
        await authenticated_client(client, db_session)

        response = await client.post(f"/api/v1/trash/projects/{trashed.id}/restore")

        assert response.status_code == 404

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.post(f"/api/v1/trash/projects/{uuid.uuid4()}/restore")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/trash/projects/{id}/permanent-delete
# ---------------------------------------------------------------------------
class TestPermanentDeleteProjectEndpoint:
    async def test_requires_authentication(self, client):
        response = await client.delete(
            f"/api/v1/trash/projects/{uuid.uuid4()}/permanent-delete"
        )

        assert response.status_code == 401

    async def test_permanently_deletes_own_trashed_project(self, client, db_session):
        user = await authenticated_client(client, db_session)
        trashed = await create_trashed_project(db_session, user.id)

        response = await client.delete(
            f"/api/v1/trash/projects/{trashed.id}/permanent-delete"
        )

        assert response.status_code == 204

        follow_up = await client.get(f"/api/v1/projects/{trashed.id}")
        assert follow_up.status_code == 404

    async def test_returns_404_for_other_users_project(self, client, db_session):
        owner = await register_via_service(db_session)
        trashed = await create_trashed_project(db_session, owner.id)
        await authenticated_client(client, db_session)

        response = await client.delete(
            f"/api/v1/trash/projects/{trashed.id}/permanent-delete"
        )

        assert response.status_code == 404

    async def test_returns_404_for_unknown_id(self, client, db_session):
        await authenticated_client(client, db_session)

        response = await client.delete(
            f"/api/v1/trash/projects/{uuid.uuid4()}/permanent-delete"
        )

        assert response.status_code == 404
