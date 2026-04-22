from __future__ import annotations

"""Deprecated compatibility layer for legacy data-scope injection.

New code must depend on ``IDataScopeResolver`` instead of importing this module.
This module is retained only as a temporary compatibility shell and currently
has no in-repository callers.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from common.exceptions import BusinessError, NotFoundError
from core.dependencies import get_db
from modules.admin.application.data_permission_resolver import (
    DataPermissionResolver,
    build_data_permission_resolver,
)
from modules.admin.application.resource_registry import (
    ResourceAction,
    resource_registry,
)


class DataPermissionContext:
    """旧数据权限入口的兼容包装.

    Deprecated:
        仅保留给仓库外部的历史调用方，仓库内新代码与后续重构统一依赖
        IDataScopeResolver。
    """

    def __init__(
        self, resource_action: ResourceAction, resolver: DataPermissionResolver
    ):
        self.resource_action = resource_action
        self.resolver = resolver

    async def build_query_scope(self, *, user, model_cls):
        return await self.resolver.build_query_scope(
            user=user,
            resource_type=self.resource_action.resource_type,
            action=self.resource_action.action,
            model_cls=model_cls,
        )

    async def resolve_scope(self, *, user, action: str | None = None) -> str:
        return await self.resolver.resolve_scope(
            user=user,
            resource_type=self.resource_action.resource_type,
            action=action or self.resource_action.action,
        )

    async def ensure_entity_allowed(self, *, user, entity):
        allowed = await self.resolver.can_operate_entity(
            user=user,
            resource_type=self.resource_action.resource_type,
            action=self.resource_action.action,
            entity=entity,
        )
        if not allowed:
            raise BusinessError("无数据操作权限", code=403)
        return entity

    async def ensure_exists_and_allowed(self, *, user, entity, not_found_message: str):
        if entity is None:
            raise NotFoundError(not_found_message)
        return await self.ensure_entity_allowed(user=user, entity=entity)


def resolve_resource_action(request: Request) -> ResourceAction:
    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)
    action = resource_registry.resolve(route_path, request.method)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resource mapping not found",
        )
    return action


async def get_data_permission_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DataPermissionContext:
    resource_action = resolve_resource_action(request)
    resolver = build_data_permission_resolver(db)
    return DataPermissionContext(resource_action=resource_action, resolver=resolver)
