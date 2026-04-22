import asyncio
import os
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import Settings, get_settings

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


async def ensure_database_exists(setting: Settings) -> None:
    database_url = setting.database_url
    database_obj = make_url(database_url)
    database_name = database_obj.database

    print(f"正在检查数据库是否存在: {database_name}")
    base_url = database_obj.set(
        database="").render_as_string(hide_password=False)

    sql = text(f"CREATE DATABASE IF NOT EXISTS {database_name}")
    if "mysql" in database_obj.drivername:
        sql = text(
            f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )

    engine = create_async_engine(base_url)

    try:
        async with engine.connect() as conn:
            await conn.execute(sql)
            await conn.commit()
        print("创建数据库成功")
    except Exception as e:
        print(f"创建数据库失败, {e}")
    finally:
        await engine.dispose()


def run_alembic_migrations(setting: Settings):
    database_url = setting.database_url

    print("正在执行Alembic数据库迁移")
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
        print("Alembic 数据库迁移完成")
    except Exception as e:
        print(f"Alembic 数据库迁移失败, {e}")
        sys.exit(1)


async def create_initial_data(settings: Settings) -> None:
    print("Step 1️⃣: 检查数据库是否创建, 没有创建则尝试创建")
    await ensure_database_exists(settings)

    print("Step 2️⃣: 执行数据库迁移脚本")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_alembic_migrations, settings)

    print("初始化完成")


if __name__ == "__main__":
    settings = get_settings()
    asyncio.run(create_initial_data(settings))
