import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.exceptions import UnauthorizedError
from src.db.session import get_db
from src.models.user import User
from src.services.auth.exceptions import InvalidTokenError
from src.services.auth.token_service import TokenService

ACCESS_TOKEN_COOKIE_NAME = "access_token"


async def get_current_user_id(
    request: Request, session: AsyncSession = Depends(get_db)
) -> uuid.UUID:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if token is None:
        raise UnauthorizedError("Authentication required")

    try:
        return TokenService(session).verify_access_token(token)
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user
