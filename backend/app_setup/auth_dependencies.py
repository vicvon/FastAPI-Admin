from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app_setup.permission_providers import get_permission_provider_bundle
from common.auth import CurrentPrincipal
from common.exceptions import AuthenticationError, PermissionError
from common.ports import (
    ICurrentPrincipalResolver,
    IDataScopeResolver,
    IPermissionChecker,
    IPermissionManager,
)
from core.logger import get_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
logger = get_logger(__name__)


def get_permission_manager(request: Request) -> IPermissionManager:
    manager = get_permission_provider_bundle(request.app).manager
    if manager is None:
        raise RuntimeError("Permission manager is not initialized")
    return manager


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


def get_current_principal_resolver(request: Request) -> ICurrentPrincipalResolver:
    resolver = get_permission_provider_bundle(request.app).principal_resolver
    if resolver is None:
        raise RuntimeError("Current principal resolver is not initialized")
    return resolver


async def _resolve_current_principal(
    token: str = Depends(oauth2_scheme),
    resolver: ICurrentPrincipalResolver = Depends(get_current_principal_resolver),
) -> CurrentPrincipal:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        return await resolver.resolve(token)
    except AuthenticationError:
        logger.opt(exception=True).debug("auth.current_principal_resolve_failed")
        raise credentials_exception


async def get_current_principal(
    principal: CurrentPrincipal = Depends(_resolve_current_principal),
) -> CurrentPrincipal:
    return principal


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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=exc.message
            )
        return current_user

    return dependency
