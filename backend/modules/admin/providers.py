from __future__ import annotations

from fastapi import FastAPI

from app_setup.permission_providers import get_permission_provider_bundle
from core.database import AsyncSession, engine
from modules.admin.application.data_scope_resolver import AdminDataScopeResolver
from modules.admin.application.principal_resolver import AdminCurrentPrincipalResolver


def register_admin_module_providers(app: FastAPI) -> None:
    """注册 admin 模块对共享身份与数据权限的实现。"""

    bundle = get_permission_provider_bundle(app)
    bundle.principal_resolver = AdminCurrentPrincipalResolver(
        session_factory=lambda: AsyncSession(engine, expire_on_commit=False)
    )
    bundle.data_scope_resolver = AdminDataScopeResolver(
        session_factory=lambda: AsyncSession(engine, expire_on_commit=False)
    )
