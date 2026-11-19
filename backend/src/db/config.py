import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool


def get_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        url=os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/codelearning",
        ),
        pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "10")),
        pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "1800")),
        pool_pre_ping=True,
    )
