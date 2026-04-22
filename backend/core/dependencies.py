from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get DB session
    """
    async for session in get_session():
        yield session
