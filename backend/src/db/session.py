from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.config import get_database_config

config = get_database_config()

engine = create_async_engine(
    config.url,
    pool_pre_ping=config.pool_pre_ping,
    pool_size=config.pool_size,
    max_overflow=config.max_overflow,
    pool_timeout=config.pool_timeout,
    pool_recycle=config.pool_recycle,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
