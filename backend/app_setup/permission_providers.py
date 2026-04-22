from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import FastAPI

from common.ports import (
    ICurrentPrincipalResolver,
    IDataScopeResolver,
    IPermissionChecker,
    IPermissionManager,
)
from core.database import AsyncSession, engine
from modules.iam.application import PermissionCheckerImpl, PermissionManagerImpl
from modules.iam.domain import RbacDomainService
from modules.iam.infra import (
    get_iam_enforcer,
    has_iam_enforcer,
    shutdown_iam_watcher,
)


@dataclass(slots=True)
class PermissionProviderBundle:
    checker: IPermissionChecker | None = None
    manager: IPermissionManager | None = None
    principal_resolver: ICurrentPrincipalResolver | None = None
    data_scope_resolver: IDataScopeResolver | None = None


def build_permission_manager(
    session_factory: Callable[[], AsyncSession],
) -> IPermissionManager:
    return PermissionManagerImpl(session_factory=session_factory)


def init_permission_provider_bundle(app: FastAPI) -> None:
    """初始化权限 provider 注册位, 后续由 app_setup 统一装配具体实现。"""

    if getattr(app.state, "permission_providers", None) is None:
        rbac_service = RbacDomainService(get_iam_enforcer())
        app.state.permission_providers = PermissionProviderBundle(
            checker=PermissionCheckerImpl(rbac_service),
            manager=build_permission_manager(
                session_factory=lambda: AsyncSession(engine, expire_on_commit=False)
            ),
        )


def get_permission_provider_bundle(app: FastAPI) -> PermissionProviderBundle:
    bundle = getattr(app.state, "permission_providers", None)
    if bundle is None:
        init_permission_provider_bundle(app)
        bundle = app.state.permission_providers
    return bundle


def shutdown_permission_runtime(app: FastAPI) -> None:
    """通过权限 provider 收口 IAM 运行时关闭逻辑。"""

    if getattr(app.state, "permission_providers", None) is None:
        return
    if not has_iam_enforcer():
        return

    watcher = getattr(get_iam_enforcer(), "watcher", None)
    if watcher is not None and hasattr(watcher, "close"):
        shutdown_iam_watcher()
