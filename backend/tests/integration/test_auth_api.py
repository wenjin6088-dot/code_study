"""Integration/contract tests for the Authentication API (RED phase).

Covers tasks:
- T028 POST /api/v1/auth/register
- T029 POST /api/v1/auth/login
- T029A GET  /api/v1/auth/me
- T030 POST /api/v1/auth/logout
- T031 POST /api/v1/auth/refresh

These endpoints do not exist yet (backend/src/api/auth.py has not been created
and is not registered on api_router), so every test in this file is expected
to FAIL until the GREEN phase implements them.

Expected contract these tests encode (for the implementer):
- Auth is cookie-based: successful login/refresh set httponly cookies
  "access_token" and "refresh_token" (not Authorization headers).
- register/login/me return a JSON user object containing at least
  "id", "email", "skill_level" and MUST NOT leak "password" or
  "password_hash".
- All errors use the existing AppException -> {"error": {"message": ...}}
  envelope already wired up in src/main.py.
"""

import uuid

import httpx
import pytest
import pytest_asyncio
from jose import jwt as jose_jwt
from sqlalchemy import select

from src.api.dependencies import ACCESS_TOKEN_COOKIE_NAME
from src.db.session import get_db
from src.main import app
from src.models.refresh_token import RefreshToken
from src.services.auth.token_service import TokenService
from src.services.auth.user_service import UserService
from src.utils.jwt import ALGORITHM

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
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


async def register_via_service(db_session, email: str, password: str = STRONG_PASSWORD):
    return await UserService(db_session).register(email=email, password=password)


async def issue_tokens(db_session, user_id):
    return await TokenService(db_session).issue_tokens(user_id)


class TestRegister:
    async def test_register_returns_201_with_user_payload(self, client):
        email = unique_email()

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": STRONG_PASSWORD},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == email
        assert "id" in body
        assert "password" not in body
        assert "password_hash" not in body

    async def test_register_rejects_duplicate_email_with_409(self, client, db_session):
        email = unique_email()
        await register_via_service(db_session, email)

        response = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": STRONG_PASSWORD},
        )

        assert response.status_code == 409
        assert "message" in response.json()["error"]

    async def test_register_rejects_invalid_email_format(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": STRONG_PASSWORD},
        )

        assert response.status_code == 400
        assert "message" in response.json()["error"]

    async def test_register_rejects_weak_password(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email(), "password": "weak"},
        )

        assert response.status_code == 400
        assert "message" in response.json()["error"]

    async def test_register_rejects_missing_fields(self, client):
        response = await client.post("/api/v1/auth/register", json={})

        assert response.status_code == 422


class TestLogin:
    async def test_login_returns_200_and_sets_auth_cookies(self, client, db_session):
        email = unique_email()
        await register_via_service(db_session, email)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": STRONG_PASSWORD},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == email
        assert "password" not in body
        assert "password_hash" not in body
        assert response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

    async def test_login_sets_httponly_cookies(self, client, db_session):
        email = unique_email()
        await register_via_service(db_session, email)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": STRONG_PASSWORD},
        )

        set_cookie_headers = response.headers.get_list("set-cookie")
        assert any(
            ACCESS_TOKEN_COOKIE_NAME in h and "httponly" in h.lower()
            for h in set_cookie_headers
        )
        assert any(
            REFRESH_TOKEN_COOKIE_NAME in h and "httponly" in h.lower()
            for h in set_cookie_headers
        )

    async def test_login_rejects_wrong_password_with_401(self, client, db_session):
        email = unique_email()
        await register_via_service(db_session, email)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword1"},
        )

        assert response.status_code == 401
        assert "message" in response.json()["error"]

    async def test_login_rejects_unknown_email_with_401(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": unique_email(), "password": STRONG_PASSWORD},
        )

        assert response.status_code == 401
        assert "message" in response.json()["error"]


class TestMe:
    async def test_me_returns_current_user_with_valid_access_token(
        self, client, db_session
    ):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == email
        assert "password" not in body
        assert "password_hash" not in body

    async def test_me_rejects_missing_cookie_with_401(self, client):
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_me_rejects_garbage_token_with_401(self, client):
        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, "garbage-token")
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_me_rejects_refresh_token_used_as_access_token(
        self, client, db_session
    ):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.refresh_token)
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_me_rejects_expired_access_token(self, client, db_session):
        from datetime import UTC, datetime, timedelta

        email = unique_email()
        user = await register_via_service(db_session, email)
        expired_token = jose_jwt.encode(
            {
                "sub": str(user.id),
                "type": "access",
                "exp": datetime.now(UTC) - timedelta(minutes=1),
            },
            "test-access-secret",
            algorithm=ALGORITHM,
        )

        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, expired_token)
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestLogout:
    async def test_logout_revokes_refresh_token_and_returns_success(
        self, client, db_session
    ):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code in (200, 204)

        from src.utils.security import hash_token

        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(pair.refresh_token)
            )
        )
        stored = result.scalar_one()
        assert stored.revoked is True

    async def test_logout_is_idempotent_for_unknown_token(self, client):
        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, "unknown-token-value")
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code in (200, 204)

    async def test_logout_is_idempotent_for_already_revoked_token(
        self, client, db_session
    ):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)
        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        first = await client.post("/api/v1/auth/logout")
        assert first.status_code in (200, 204)

        second = await client.post("/api/v1/auth/logout")

        assert second.status_code in (200, 204)

    async def test_logout_without_cookie_does_not_error(self, client):
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code in (200, 204)

    async def test_logout_clears_auth_cookies(self, client, db_session):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(ACCESS_TOKEN_COOKIE_NAME, pair.access_token)
        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code in (200, 204)
        set_cookie_headers = response.headers.get_list("set-cookie")

        def _is_cleared(name: str) -> bool:
            for h in set_cookie_headers:
                if name not in h:
                    continue
                lowered = h.lower()
                if "max-age=0" in lowered or "01 jan 1970" in lowered:
                    return True
            return False

        assert _is_cleared(ACCESS_TOKEN_COOKIE_NAME), set_cookie_headers
        assert _is_cleared(REFRESH_TOKEN_COOKIE_NAME), set_cookie_headers


class TestRefresh:
    async def test_refresh_rotates_tokens_and_returns_200(self, client, db_session):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 200
        new_access = response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        new_refresh = response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        assert new_access
        assert new_refresh
        assert new_refresh != pair.refresh_token

    async def test_refresh_revokes_old_refresh_token(self, client, db_session):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        await client.post("/api/v1/auth/refresh")

        from src.utils.security import hash_token

        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(pair.refresh_token)
            )
        )
        old_record = result.scalar_one()
        assert old_record.revoked is True

    async def test_refresh_rejects_missing_cookie_with_401(self, client):
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401

    async def test_refresh_rejects_garbage_token_with_401(self, client):
        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, "garbage-token")
        response = await client.post("/api/v1/auth/refresh")

        assert response.status_code == 401

    async def test_refresh_rejects_reused_rotated_token_with_401(
        self, client, db_session
    ):
        email = unique_email()
        user = await register_via_service(db_session, email)
        pair = await issue_tokens(db_session, user.id)

        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        first = await client.post("/api/v1/auth/refresh")
        assert first.status_code == 200

        client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, pair.refresh_token)
        second = await client.post("/api/v1/auth/refresh")

        assert second.status_code == 401
