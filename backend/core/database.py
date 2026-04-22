from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from config.settings import get_settings

settings = get_settings()

# Ensure the database URL uses an async driver
database_url = settings.database_url
if database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+aiomysql://")
elif database_url.startswith("mysql+pymysql://"):
    database_url = database_url.replace("mysql+pymysql://", "mysql+aiomysql://")

engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
