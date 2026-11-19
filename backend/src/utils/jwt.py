import os
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _access_secret() -> str:
    return os.environ["JWT_SECRET_KEY"]


def _refresh_secret() -> str:
    return os.environ["JWT_REFRESH_SECRET"]


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "type": "access", "exp": expire, "jti": uuid.uuid4().hex}
    return jwt.encode(payload, _access_secret(), algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": subject,
        "type": "refresh",
        "exp": expire,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _refresh_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, _access_secret(), algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type: expected access token")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = jwt.decode(token, _refresh_secret(), algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type: expected refresh token")
    return payload
