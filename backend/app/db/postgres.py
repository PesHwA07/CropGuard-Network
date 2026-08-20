"""Async PostgreSQL connection via SQLAlchemy.

Provides:
- engine: async engine (used at app startup/shutdown)
- get_db: FastAPI dependency yielding an AsyncSession per request
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request, auto-closes."""
    async with AsyncSessionLocal() as session:
        yield session
