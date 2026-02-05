"""FastAPI dependency injection."""

from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.company import Company


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inject async database session."""
    async for session in get_async_session():
        yield session


async def get_company_by_id(
    company_id: UUID,
    session: AsyncSession,
    *,
    allow_inactive: bool = False,
) -> Company | None:
    """Load company by id; optionally filter by is_active."""
    q = select(Company).where(Company.id == company_id)
    if not allow_inactive:
        q = q.where(Company.is_active.is_(True))
    result = await session.execute(q)
    return result.scalar_one_or_none()
