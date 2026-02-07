"""Async database session."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


def _get_async_url() -> str:
    url = get_settings().database_url
    if url.startswith("postgresql+psycopg2"):
        return url.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Base(DeclarativeBase):
    pass


_engine = create_async_engine(
    _get_async_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
