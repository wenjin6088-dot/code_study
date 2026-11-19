import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.services.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidEmailError,
    WeakPasswordError,
)
from src.utils.security import hash_password, hash_token, verify_password

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LENGTH = 8


class UserService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def register(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if not EMAIL_PATTERN.match(normalized_email):
            raise InvalidEmailError(f"Invalid email format: {email}")
        _validate_password_strength(password)

        existing = await self._session.execute(
            select(User).where(User.email == normalized_email)
        )
        if existing.scalar_one_or_none() is not None:
            raise EmailAlreadyRegisteredError(
                f"Email already registered: {normalized_email}"
            )

        user = User(email=normalized_email, password_hash=hash_password(password))
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyRegisteredError(
                f"Email already registered: {normalized_email}"
            ) from exc
        await self._session.refresh(user)
        return user

    async def login(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        result = await self._session.execute(
            select(User).where(User.email == normalized_email)
        )
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        user.last_login_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is None or token.revoked:
            return

        token.revoked = True
        token.revoked_at = datetime.now(UTC)
        await self._session.commit()


def _validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise WeakPasswordError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise WeakPasswordError("Password must contain both letters and numbers")
