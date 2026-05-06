import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

from alembic import context
from config.settings import get_settings

# 将项目根目录加入 sys.path, 确保能导入项目模块
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# 必须导入你的模型, 这样 SQLModel.metadata 才能发现表结构
# 注意: 这里导入 modules.admin.domain.entities 替代 infra.model
# 因为我们已经在 entities.py 中定义了新结构
from modules.admin.domain import entities  # noqa: F401, E402
from modules.label_manager.domain import entities # noqa: F401, E402

# 如果有其他模块的 model 也需要在这里导入


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def _include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "casbin_rule":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=_include_object,
        compare_server_default=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """实际执行迁移的同步函数，将被 run_sync 调用"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=_include_object,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    """异步执行迁移逻辑"""
    configuration = config.get_section(config.config_ini_section)
    assert configuration is not None

    # 从 settings 中覆盖数据库 URL
    configuration["sqlalchemy.url"] = get_settings().database_url

    # 使用 async_engine_from_config 创建异步引擎
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # 关键点：使用 run_sync 在异步连接上执行同步的迁移代码
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # 使用 asyncio.run 启动异步流程
    asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
