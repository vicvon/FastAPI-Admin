from __future__ import annotations

from collections.abc import Callable

from sqlmodel.ext.asyncio.session import AsyncSession

from common.auth import CurrentPrincipal
from common.ports import IDataScopeResolver
from modules.admin.application.data_permission_resolver import (
    build_data_permission_resolver,
)


class AdminDataScopeResolver(IDataScopeResolver):
    """基于现有 admin 数据权限实现的 Port 适配器。"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def resolve_scope(self, user_id: int, resource_type: str, action: str) -> str:
        async with self._session_factory() as session:
            resolver = build_data_permission_resolver(session)
            return await resolver.resolve_scope(
                user=CurrentPrincipal(
                    user_id=user_id,
                    username="",
                    is_active=True,
                    token_version=0,
                ),
                resource_type=resource_type,
                action=action,
            )

    async def build_query_scope(
        self,
        user_id: int,
        resource_type: str,
        action: str,
        model_cls: type[object],
    ):
        async with self._session_factory() as session:
            resolver = build_data_permission_resolver(session)
            return await resolver.build_query_scope(
                user=CurrentPrincipal(
                    user_id=user_id,
                    username="",
                    is_active=True,
                    token_version=0,
                ),
                resource_type=resource_type,
                action=action,
                model_cls=model_cls,
            )

    async def can_operate_entity(
        self,
        user_id: int,
        resource_type: str,
        action: str,
        entity: object,
    ) -> bool:
        async with self._session_factory() as session:
            resolver = build_data_permission_resolver(session)
            return await resolver.can_operate_entity(
                user=CurrentPrincipal(
                    user_id=user_id,
                    username="",
                    is_active=True,
                    token_version=0,
                ),
                resource_type=resource_type,
                action=action,
                entity=entity,
            )
