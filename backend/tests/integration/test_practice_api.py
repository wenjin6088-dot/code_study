"""Integration tests for:
- T120: GET /api/v1/tasks/{task_id}/practice
- T121: GET /api/v1/tasks/{task_id}/practice/{problem_number}

Reuses the auth/client/project helpers from test_tasks_api.py.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from src.db.session import get_db
from src.main import app
from src.models.practice_problem import PracticeProblem
from src.services.ai.prompts import PRACTICE_PROBLEM_TYPES
from src.services.task_service import TaskService
from tests.integration.test_tasks_api import (
    authenticated_client,
    create_project,
    register_via_service,
)


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


async def _make_task(db_session, user):
    project = await create_project(db_session, user.id)
    return await TaskService(db_session).create(
        user_id=user.id, project_id=project.id, title="A task"
    )


async def _insert_problems(db_session, task_id) -> list[PracticeProblem]:
    problems = [
        PracticeProblem(
            task_id=task_id,
            problem_number=number,
            problem_type=problem_type,
            problem_statement=f"Statement {number}",
            learning_objective=f"Objective {number}",
            hints=["Hint 1", "Hint 2"],
            model_solution=f"Solution {number}",
            expected_output=f"Output {number}",
        )
        for number, problem_type in enumerate(PRACTICE_PROBLEM_TYPES, 1)
    ]
    db_session.add_all(problems)
    await db_session.commit()
    return problems


class TestGetPracticeProblemsEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        task = await _make_task(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice")

        assert response.status_code == 401

    async def test_returns_404_task_not_found_for_unknown_task(
        self, client, db_session
    ):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/practice")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_404_task_not_found_for_other_users_task(
        self, client, db_session
    ):
        owner = await register_via_service(db_session)
        task = await _make_task(db_session, owner)
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_pending_status_with_empty_list_when_no_problems(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice")

        assert response.status_code == 200
        body = response.json()
        assert body == {"task_id": str(task.id), "status": "pending", "problems": []}

    async def test_returns_completed_status_with_five_problems_in_order(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task(db_session, user)
        await _insert_problems(db_session, task.id)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert len(body["problems"]) == 5
        assert [p["problem_number"] for p in body["problems"]] == [1, 2, 3, 4, 5]
        assert body["problems"][0]["problem_type"] == "follow_along"
        assert body["problems"][0]["hints"] == ["Hint 1", "Hint 2"]
        assert body["problems"][0]["model_solution"] == "Solution 1"


class TestGetSinglePracticeProblemEndpoint:
    async def test_requires_authentication(self, client, db_session):
        user = await register_via_service(db_session)
        task = await _make_task(db_session, user)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice/1")

        assert response.status_code == 401

    async def test_returns_404_task_not_found_for_unknown_task(
        self, client, db_session
    ):
        await authenticated_client(client, db_session)

        response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/practice/1")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Task not found"

    async def test_returns_404_when_problem_number_does_not_exist(
        self, client, db_session
    ):
        user = await authenticated_client(client, db_session)
        task = await _make_task(db_session, user)
        await _insert_problems(db_session, task.id)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice/99")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Practice problem not found"

    async def test_returns_requested_problem(self, client, db_session):
        user = await authenticated_client(client, db_session)
        task = await _make_task(db_session, user)
        await _insert_problems(db_session, task.id)

        response = await client.get(f"/api/v1/tasks/{task.id}/practice/3")

        assert response.status_code == 200
        body = response.json()
        assert body["problem_number"] == 3
        assert body["problem_type"] == "modify"
        assert body["problem_statement"] == "Statement 3"
