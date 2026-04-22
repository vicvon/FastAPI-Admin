from __future__ import annotations

from collections.abc import Callable

from sqlmodel.ext.asyncio.session import AsyncSession

from common.ports import IPermissionManager
from modules.iam.application.policy_projector import (
    sync_policies_from_db,
    sync_role_api_policies_incremental,
    sync_user_role_grouping_incremental,
)
from modules.iam.infra.enforcer import get_iam_enforcer, refresh_iam_enforcer


class PermissionManagerImpl(IPermissionManager):
    """基于当前 Casbin 运行时实现的权限投影管理器。"""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
    ):
        self._session_factory = session_factory

    async def sync_role_policies(self, role_id: int) -> None:
        async with self._session_factory() as session:
            await sync_role_api_policies_incremental(
                session, get_iam_enforcer(), role_id
            )

    async def sync_user_roles(self, user_id: int) -> None:
        async with self._session_factory() as session:
            await sync_user_role_grouping_incremental(
                session, get_iam_enforcer(), user_id
            )

    async def refresh_all(self) -> None:
        async with self._session_factory() as session:
            refresh_iam_enforcer()
            await sync_policies_from_db(session, get_iam_enforcer())
