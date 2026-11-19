import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt as jose_jwt
from sqlalchemy import select

from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.services.auth.exceptions import InvalidTokenError
from src.services.auth.token_service import TokenService
from src.utils.jwt import ALGORITHM, decode_access_token
from src.utils.security import hash_token


@pytest.fixture(autouse=True)
def _jwt_secrets(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-access-secret")
    monkeypatch.setenv("JWT_REFRESH_SECRET", "test-refresh-secret")


async def create_user(db_session) -> User:
    user = User(
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="irrelevant-hash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestIssueTokens:
    async def test_issue_tokens_returns_valid_access_and_refresh_tokens(
        self, db_session
    ):
        service = TokenService(db_session)
        user = await create_user(db_session)

        pair = await service.issue_tokens(user.id)

        payload = decode_access_token(pair.access_token)
        assert payload["sub"] == str(user.id)

    async def test_issue_tokens_stores_hashed_refresh_token_in_db(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)

        pair = await service.issue_tokens(user.id)

        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(pair.refresh_token)
            )
        )
        stored = result.scalar_one()
        assert stored.user_id == user.id
        assert stored.revoked is False

    async def test_issue_tokens_never_stores_plaintext_refresh_token(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)

        pair = await service.issue_tokens(user.id)

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
        stored = result.scalar_one()
        assert stored.token_hash != pair.refresh_token


class TestVerifyAccessToken:
    async def test_verify_access_token_returns_user_id_for_valid_token(
        self, db_session
    ):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)

        user_id = service.verify_access_token(pair.access_token)

        assert user_id == user.id

    async def test_verify_access_token_rejects_refresh_token(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)

        with pytest.raises(InvalidTokenError):
            service.verify_access_token(pair.refresh_token)

    async def test_verify_access_token_rejects_garbage_token(self, db_session):
        service = TokenService(db_session)

        with pytest.raises(InvalidTokenError):
            service.verify_access_token("not-a-real-token")

    async def test_verify_access_token_rejects_expired_token(
        self, db_session, monkeypatch
    ):
        service = TokenService(db_session)
        user = await create_user(db_session)
        expired_payload = {
            "sub": str(user.id),
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        }
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
        expired_token = jose_jwt.encode(
            expired_payload, "test-secret-key", algorithm=ALGORITHM
        )

        with pytest.raises(InvalidTokenError):
            service.verify_access_token(expired_token)


class TestRotateRefreshToken:
    async def test_rotate_issues_new_token_pair(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)

        new_pair = await service.rotate_refresh_token(pair.refresh_token)

        assert new_pair.refresh_token != pair.refresh_token
        assert new_pair.access_token != pair.access_token
        payload = decode_access_token(new_pair.access_token)
        assert payload["sub"] == str(user.id)

    async def test_rotate_revokes_old_refresh_token(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)

        await service.rotate_refresh_token(pair.refresh_token)

        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(pair.refresh_token)
            )
        )
        old_record = result.scalar_one()
        assert old_record.revoked is True
        assert old_record.revoked_at is not None

    async def test_rotate_rejects_already_revoked_token(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)
        await service.rotate_refresh_token(pair.refresh_token)

        with pytest.raises(InvalidTokenError):
            await service.rotate_refresh_token(pair.refresh_token)

    async def test_rotate_rejects_unknown_token(self, db_session):
        service = TokenService(db_session)
        user = await create_user(db_session)
        subject = str(user.id)
        unknown_token = jose_jwt.encode(
            {
                "sub": subject,
                "type": "refresh",
                "exp": datetime.now(UTC) + timedelta(days=7),
            },
            "unused-but-unknown-secret",
            algorithm=ALGORITHM,
        )

        with pytest.raises(InvalidTokenError):
            await service.rotate_refresh_token(unknown_token)

    async def test_rotate_rejects_expired_db_record(self, db_session, monkeypatch):
        service = TokenService(db_session)
        user = await create_user(db_session)
        pair = await service.issue_tokens(user.id)

        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(pair.refresh_token)
            )
        )
        stored = result.scalar_one()
        stored.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await db_session.commit()

        with pytest.raises(InvalidTokenError):
            await service.rotate_refresh_token(pair.refresh_token)
