import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.services.auth.exceptions import InvalidTokenError
from src.utils.jwt import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from src.utils.security import hash_token


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


class TokenService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def issue_tokens(self, user_id: uuid.UUID) -> TokenPair:
        subject = str(user_id)
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        self._add_refresh_token_record(user_id, refresh_token)
        await self._session.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def verify_access_token(self, access_token: str) -> uuid.UUID:
        try:
            payload = decode_access_token(access_token)
        except JWTError as exc:
            raise InvalidTokenError("Invalid or expired access token") from exc
        return uuid.UUID(payload["sub"])

    async def rotate_refresh_token(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise InvalidTokenError("Invalid or expired refresh token") from exc

        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(refresh_token)
            )
        )
        stored = result.scalar_one_or_none()
        if stored is None or stored.revoked:
            raise InvalidTokenError("Refresh token has been revoked or does not exist")

        now = datetime.now(UTC)
        if stored.expires_at <= now:
            raise InvalidTokenError("Refresh token has expired")

        stored.revoked = True
        stored.revoked_at = now

        user_id = uuid.UUID(payload["sub"])
        subject = payload["sub"]
        access_token = create_access_token(subject)
        new_refresh_token = create_refresh_token(subject)
        self._add_refresh_token_record(user_id, new_refresh_token)

        await self._session.commit()
        return TokenPair(access_token=access_token, refresh_token=new_refresh_token)

    def _add_refresh_token_record(self, user_id: uuid.UUID, refresh_token: str) -> None:
        expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        self._session.add(
            RefreshToken(
                user_id=user_id,
                token_hash=hash_token(refresh_token),
                expires_at=expires_at,
            )
        )
