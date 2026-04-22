from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app_setup.permission_providers import get_permission_provider_bundle
from common.auth import CurrentPrincipal
from common.exceptions import AuthenticationError, PermissionError
from common.ports import IDataScopeResolver, IPermissionChecker, IPermissionManager
from core.context import RequestContext
from core.dependencies import get_db
from core.logger import get_logger
from core.security import CaptchaService, TokenService, decode_access_token
from modules.admin.application.services import (
    PermissionService,
    RolePermissionApplicationService,
    RoleService,
    UserService,
)
from modules.admin.domain.entities import User
from modules.admin.infra.repositories import (
    PermissionRepository,
    RoleGrantJobRepository,
    RoleRepository,
    ScopeRuleRepository,
    UserRepository,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
logger = get_logger(__name__)


def get_permission_manager(request: Request) -> IPermissionManager:
    manager = get_permission_provider_bundle(request.app).manager
    if manager is None:
        raise RuntimeError("Permission manager is not initialized")
    return manager


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


async def _resolve_authenticated_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except ValueError:
        logger.opt(exception=True).debug("JWT decode failed")
        raise credentials_exception

    token_service = TokenService()
    if await token_service.is_access_token_revoked(payload):
        raise credentials_exception

    sub = payload.get("sub")
    if not sub:
        raise credentials_exception
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception

    user = await user_repo.get(user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    if int(payload.get("tv", 0)) != int(user.token_version):
        raise credentials_exception

    RequestContext.set_user_id(user.id)
    RequestContext.set_user_name(user.username)
    return user


async def get_current_user(
    user: User = Depends(_resolve_authenticated_user),
) -> User:
    return user


async def get_current_principal(
    user: User = Depends(_resolve_authenticated_user),
) -> CurrentPrincipal:
    return CurrentPrincipal(
        user_id=int(user.id),
        username=user.username,
        is_active=bool(user.is_active),
        token_version=int(user.token_version),
    )


def get_permission_checker(request: Request) -> IPermissionChecker:
    checker = get_permission_provider_bundle(request.app).checker
    if checker is None:
        raise RuntimeError("Permission checker is not initialized")
    return checker


def get_data_scope_resolver(request: Request) -> IDataScopeResolver:
    resolver = get_permission_provider_bundle(request.app).data_scope_resolver
    if resolver is None:
        raise RuntimeError("Data scope resolver is not initialized")
    return resolver


def require_permission():
    async def dependency(
        request: Request,
        current_user: CurrentPrincipal = Depends(get_current_principal),
        checker: IPermissionChecker = Depends(get_permission_checker),
    ) -> CurrentPrincipal:
        if current_user.user_id is None:
            raise AuthenticationError("用户认证失败")
        obj = request.url.path
        act = request.method.upper()
        try:
            await checker.check_permission(current_user.user_id, obj, act)
        except PermissionError as exc:
            logger.warning(
                "auth.permission_denied sub={} obj={} act={} user_id={}",
                current_user.subject,
                obj,
                act,
                current_user.user_id,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
        return current_user

    return dependency
