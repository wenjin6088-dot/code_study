import uuid

import httpx
import pytest
from fastapi import Depends, FastAPI

from src.api.dependencies import (
    ACCESS_TOKEN_COOKIE_NAME,
    get_current_user,
    get_current_user_id,
)
from src.api.exceptions import register_exception_handlers
from src.db.session import get_db
from src.models.user import User
from src.services.auth.token_service import TokenService


@pytest.fixture(autouse=True)
def _jwt_secrets(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")


def build_app(db_session) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protected/id")
    async def protected_id(user_id: uuid.UUID = Depends(get_current_user_id)):
        return {"user_id": str(user_id)}

    @app.get("/protected/user")
    async def protected_user(user: User = Depends(get_current_user)):
        return {"email": user.email}

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


def make_client(app: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def create_user(db_session) -> User:
    user = User(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com", password_hash="irrelevant"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetCurrentUserId:
    async def test_rejects_missing_cookie(self, db_session):
        app = build_app(db_session)
        async with make_client(app) as client:
            response = await client.get("/protected/id")

        assert response.status_code == 401

    async def test_rejects_invalid_token(self, db_session):
        app = build_app(db_session)
        async with make_client(app) as client:
            client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "garbage-token")
            response = await client.get("/protected/id")

        assert response.status_code == 401

    async def test_rejects_refresh_token_used_as_access_token(self, db_session):
        app = build_app(db_session)
        user = await create_user(db_session)
        pair = await TokenService(db_session).issue_tokens(user.id)

        async with make_client(app) as client:
            client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.refresh_token)
            response = await client.get("/protected/id")

        assert response.status_code == 401

    async def test_accepts_valid_access_token(self, db_session):
        app = build_app(db_session)
        user = await create_user(db_session)
        pair = await TokenService(db_session).issue_tokens(user.id)

        async with make_client(app) as client:
            client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
            response = await client.get("/protected/id")

        assert response.status_code == 200
        assert response.json()["user_id"] == str(user.id)


class TestGetCurrentUser:
    async def test_returns_full_user_entity(self, db_session):
        app = build_app(db_session)
        user = await create_user(db_session)
        pair = await TokenService(db_session).issue_tokens(user.id)

        async with make_client(app) as client:
            client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
            response = await client.get("/protected/user")

        assert response.status_code == 200
        assert response.json()["email"] == user.email

    async def test_rejects_missing_cookie(self, db_session):
        app = build_app(db_session)
        async with make_client(app) as client:
            response = await client.get("/protected/user")

        assert response.status_code == 401

    async def test_rejects_token_for_deleted_user(self, db_session):
        app = build_app(db_session)
        user = await create_user(db_session)
        pair = await TokenService(db_session).issue_tokens(user.id)
        await db_session.delete(user)
        await db_session.commit()

        async with make_client(app) as client:
            client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
            response = await client.get("/protected/user")

        assert response.status_code == 401
