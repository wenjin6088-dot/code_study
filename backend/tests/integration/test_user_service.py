import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models.refresh_token import RefreshToken
from src.services.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidEmailError,
    WeakPasswordError,
)
from src.services.auth.user_service import UserService
from src.utils.security import hash_token


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


class TestRegister:
    async def test_register_creates_user_with_hashed_password(self, db_session):
        service = UserService(db_session)
        email = unique_email()

        user = await service.register(email=email, password="Password123")

        assert user.id is not None
        assert user.email == email
        assert user.password_hash != "Password123"
        assert user.skill_level == "Complete Beginner"

    async def test_register_normalizes_email_case(self, db_session):
        service = UserService(db_session)
        email = unique_email()

        user = await service.register(email=email.upper(), password="Password123")

        assert user.email == email

    async def test_register_rejects_duplicate_email(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        await service.register(email=email, password="Password123")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(email=email, password="AnotherPass1")

    async def test_register_rejects_duplicate_email_case_insensitive(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        await service.register(email=email, password="Password123")

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(email=email.upper(), password="AnotherPass1")

    async def test_register_translates_integrity_error_on_concurrent_duplicate(
        self, db_session, monkeypatch
    ):
        # A UNIQUE-constraint violation can still reach commit() despite the
        # pre-check passing, if another connection inserts the same email in
        # between. Simulate that race by forcing commit() to raise directly.
        service = UserService(db_session)

        async def raise_integrity_error():
            raise IntegrityError(
                "INSERT",
                {},
                Exception("duplicate key value violates unique constraint"),
            )

        monkeypatch.setattr(db_session, "commit", raise_integrity_error)

        with pytest.raises(EmailAlreadyRegisteredError):
            await service.register(email=unique_email(), password="Password123")

    async def test_register_rejects_invalid_email_format(self, db_session):
        service = UserService(db_session)

        with pytest.raises(InvalidEmailError):
            await service.register(email="not-an-email", password="Password123")

    async def test_register_rejects_short_password(self, db_session):
        service = UserService(db_session)

        with pytest.raises(WeakPasswordError):
            await service.register(email=unique_email(), password="Pass1")

    async def test_register_rejects_password_without_digit(self, db_session):
        service = UserService(db_session)

        with pytest.raises(WeakPasswordError):
            await service.register(email=unique_email(), password="NoDigitsHere")

    async def test_register_rejects_password_without_letter(self, db_session):
        service = UserService(db_session)

        with pytest.raises(WeakPasswordError):
            await service.register(email=unique_email(), password="12345678")


class TestLogin:
    async def test_login_succeeds_with_correct_credentials(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        await service.register(email=email, password="Password123")

        user = await service.login(email=email, password="Password123")

        assert user.email == email
        assert user.last_login_at is not None

    async def test_login_is_case_insensitive_on_email(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        await service.register(email=email, password="Password123")

        user = await service.login(email=email.upper(), password="Password123")

        assert user.email == email

    async def test_login_rejects_wrong_password(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        await service.register(email=email, password="Password123")

        with pytest.raises(InvalidCredentialsError):
            await service.login(email=email, password="WrongPassword1")

    async def test_login_rejects_unknown_email(self, db_session):
        service = UserService(db_session)

        with pytest.raises(InvalidCredentialsError):
            await service.login(email=unique_email(), password="Password123")


class TestLogout:
    async def test_logout_revokes_refresh_token(self, db_session):
        service = UserService(db_session)
        email = unique_email()
        user = await service.register(email=email, password="Password123")
        raw_refresh_token = "raw-refresh-token-value"

        token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            expires_at=user.created_at,
        )
        db_session.add(token)
        await db_session.commit()

        await service.logout(refresh_token=raw_refresh_token)

        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.id == token.id)
        )
        refreshed = result.scalar_one()
        assert refreshed.revoked is True
        assert refreshed.revoked_at is not None

    async def test_logout_is_idempotent_for_unknown_token(self, db_session):
        service = UserService(db_session)

        await service.logout(refresh_token="unknown-token-value")
