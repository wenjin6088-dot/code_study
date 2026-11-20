import os

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import ACCESS_TOKEN_COOKIE_NAME, get_current_user
from src.api.exceptions import AppException, ConflictError, UnauthorizedError
from src.db.session import get_db
from src.models.user import User
from src.services.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidTokenError,
    WeakPasswordError,
)
from src.services.auth.token_service import TokenPair, TokenService
from src.services.auth.user_service import UserService

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"

# The frontend and backend are deployed on different subdomains in production
# (and therefore different sites for cookie purposes), so the auth cookies
# must use SameSite=None to be sent on cross-site requests. Browsers reject
# SameSite=None cookies without Secure, so the two are tied together. Local
# dev runs both on http://localhost (same site), where Lax already works and
# Secure would block the cookie over plain HTTP.
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax")
COOKIE_SECURE = COOKIE_SAMESITE == "none"

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    skill_level: str

    model_config = {"from_attributes": True}


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, skill_level=user.skill_level)


def _first_cookie_value(request: Request, name: str) -> str | None:
    """Return the first occurrence of ``name`` in the raw Cookie header.

    ``Request.cookies`` is a dict built by iterating the header left-to-right
    and overwriting on each match, so a duplicate cookie name (e.g. a stale
    value alongside one just set by a previous response) resolves to the
    *last* value. We want the first (the one the caller explicitly intended)
    so we parse the raw header ourselves instead of trusting that dict.
    """
    header = request.headers.get("cookie")
    if not header:
        return None
    for chunk in header.split(";"):
        if "=" not in chunk:
            continue
        key, _, value = chunk.strip().partition("=")
        if key == name:
            return value
    return None


def _set_auth_cookies(response: Response, tokens: TokenPair) -> None:
    response.set_cookie(
        ACCESS_TOKEN_COOKIE_NAME,
        tokens.access_token,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        tokens.refresh_token,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_db)
) -> UserResponse:
    try:
        user = await UserService(session).register(
            email=payload.email, password=payload.password
        )
    except EmailAlreadyRegisteredError as exc:
        raise ConflictError(str(exc)) from exc
    except (InvalidEmailError, WeakPasswordError) as exc:
        raise AppException(str(exc)) from exc
    return _user_response(user)


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        user = await UserService(session).login(
            email=payload.email, password=payload.password
        )
    except InvalidCredentialsError as exc:
        raise UnauthorizedError(str(exc)) from exc

    tokens = await TokenService(session).issue_tokens(user.id)
    _set_auth_cookies(response, tokens)
    return _user_response(user)


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, session: AsyncSession = Depends(get_db)
) -> None:
    refresh_token = _first_cookie_value(request, REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        await UserService(session).logout(refresh_token)
    response.delete_cookie(
        ACCESS_TOKEN_COOKIE_NAME, samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE
    )
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE_NAME, samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE
    )


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    refresh_token = _first_cookie_value(request, REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token is None:
        raise UnauthorizedError("Refresh token required")

    try:
        tokens = await TokenService(session).rotate_refresh_token(refresh_token)
    except InvalidTokenError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user_id = TokenService(session).verify_access_token(tokens.access_token)
    user = await session.get(User, user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    _set_auth_cookies(response, tokens)
    return _user_response(user)
