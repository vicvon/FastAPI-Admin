from __future__ import annotations

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app_setup.auth_dependencies import get_permission_manager
from common.ports import IPermissionManager
from core.dependencies import get_db
from core.security import CaptchaService, TokenService
from modules.admin.application.services import (
    PermissionService,
    RolePermissionApplicationService,
    RoleService,
    UserService,
)
from modules.admin.infra.repositories import (
    PermissionRepository,
    RoleGrantJobRepository,
    RoleRepository,
    ScopeRuleRepository,
    UserRepository,
)


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(db)


def get_role_repository(
    db: AsyncSession = Depends(get_db),
) -> RoleRepository:
    return RoleRepository(db)


def get_permission_repository(
    db: AsyncSession = Depends(get_db),
) -> PermissionRepository:
    return PermissionRepository(db)


def get_scope_rule_repository(
    db: AsyncSession = Depends(get_db),
) -> ScopeRuleRepository:
    return ScopeRuleRepository(db)


def get_role_grant_job_repository(
    db: AsyncSession = Depends(get_db),
) -> RoleGrantJobRepository:
    return RoleGrantJobRepository(db)


def get_admin_auth_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(users=user_repo, roles=None)


def get_admin_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
    permission_repo: PermissionRepository = Depends(get_permission_repository),
    permission_manager: IPermissionManager = Depends(get_permission_manager),
) -> UserService:
    return UserService(
        users=user_repo,
        roles=role_repo,
        permissions=permission_repo,
        permission_manager=permission_manager,
    )


def get_admin_role_service(
    role_repo: RoleRepository = Depends(get_role_repository),
    permission_repo: PermissionRepository = Depends(get_permission_repository),
    permission_manager: IPermissionManager = Depends(get_permission_manager),
) -> RoleService:
    return RoleService(
        roles=role_repo,
        permissions=permission_repo,
        permission_manager=permission_manager,
    )


def get_admin_role_permission_app_service(
    role_repo: RoleRepository = Depends(get_role_repository),
    permission_repo: PermissionRepository = Depends(get_permission_repository),
    scope_rule_repo: ScopeRuleRepository = Depends(get_scope_rule_repository),
    grant_job_repo: RoleGrantJobRepository = Depends(get_role_grant_job_repository),
    permission_manager: IPermissionManager = Depends(get_permission_manager),
) -> RolePermissionApplicationService:
    return RolePermissionApplicationService(
        roles=role_repo,
        permissions=permission_repo,
        scope_rules=scope_rule_repo,
        permission_manager=permission_manager,
        grant_jobs=grant_job_repo,
    )


def get_admin_permission_service(
    permission_repo: PermissionRepository = Depends(get_permission_repository),
) -> PermissionService:
    return PermissionService(permission_repo)


def get_admin_token_service() -> TokenService:
    return TokenService()


def get_admin_captcha_service() -> CaptchaService:
    return CaptchaService()
