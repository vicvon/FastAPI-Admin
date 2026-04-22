import contextlib

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from config.settings import get_settings
from core.context import RequestContext
from core.logger import get_logger
from core.security import CaptchaService, TokenService
from modules.admin.api.dependencies import (
    get_admin_auth_user_service,
    get_admin_captcha_service,
    get_admin_token_service,
)
from modules.admin.api.v1.schemas import (
    CaptchaResponse,
    LogoutRequest,
    OAuth2TokenResponse,
    RefreshTokenRequest,
)
from modules.admin.application.services import UserService

router = APIRouter(prefix="/auth", tags=["认证"])
logger = get_logger(__name__)
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/token", auto_error=False
)


def _oauth2_error(
    status_code: int, *, error: str, error_description: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "error_description": error_description},
    )


def _build_token_response(access_token: str, refresh_token: str) -> OAuth2TokenResponse:
    settings = get_settings()
    return OAuth2TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(settings.access_token_expire_minutes * 60),
    )


async def _issue_tokens_after_auth(
    *,
    form_data: OAuth2PasswordRequestForm,
    service: UserService,
    token_service: TokenService,
) -> OAuth2TokenResponse | JSONResponse:
    user = await service.authenticate(form_data.username, form_data.password)
    if user is None or user.id is None:
        logger.warning(
            "auth.login_failed username={} request_id={} ip={} user_agent={}",
            form_data.username,
            RequestContext.get_request_id(),
            RequestContext.get_ip(),
            RequestContext.get_user_agent(),
        )
        return _oauth2_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="invalid_grant",
            error_description="错误的用户名或密码",
        )
    try:
        access_token, refresh_token = await token_service.issue_token_pair(
            user_id=user.id, token_version=user.token_version
        )
    except RuntimeError:
        return _oauth2_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="server_error",
            error_description="Token解析异常",
        )
    logger.info(
        "auth.login_success user_id={} username={} request_id={} ip={} user_agent={}",
        user.id,
        user.username,
        RequestContext.get_request_id(),
        RequestContext.get_ip(),
        RequestContext.get_user_agent(),
    )
    return _build_token_response(access_token=access_token, refresh_token=refresh_token)


@router.get("/captcha", response_model=CaptchaResponse, summary="获取登录验证码")
async def captcha(
    captcha_service: CaptchaService = Depends(get_admin_captcha_service),
) -> CaptchaResponse | JSONResponse:
    try:
        payload = await captcha_service.issue(
            ip=RequestContext.get_ip(),
            user_agent=RequestContext.get_user_agent(),
        )
    except RuntimeError:
        return _oauth2_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="server_error",
            error_description="获取验证码异常",
        )
    return CaptchaResponse(**payload)


@router.post("/login", response_model=OAuth2TokenResponse, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    captcha_id: str | None = Form(default=None),
    captcha_code: str | None = Form(default=None),
    service: UserService = Depends(get_admin_auth_user_service),
    token_service: TokenService = Depends(get_admin_token_service),
    captcha_service: CaptchaService = Depends(get_admin_captcha_service),
) -> OAuth2TokenResponse | JSONResponse:
    ok = await captcha_service.verify(
        captcha_id,
        captcha_code,
        ip=RequestContext.get_ip(),
        user_agent=RequestContext.get_user_agent(),
    )
    if not ok:
        return _oauth2_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="invalid_grant",
            error_description="非法验证码",
        )
    return await _issue_tokens_after_auth(
        form_data=form_data, service=service, token_service=token_service
    )


@router.post("/token", response_model=OAuth2TokenResponse, summary="获取访问令牌")
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_admin_auth_user_service),
    token_service: TokenService = Depends(get_admin_token_service),
) -> OAuth2TokenResponse | JSONResponse:
    return await _issue_tokens_after_auth(
        form_data=form_data, service=service, token_service=token_service
    )


@router.post("/refresh", response_model=OAuth2TokenResponse, summary="刷新访问令牌")
async def refresh_token(
    data: RefreshTokenRequest,
    token_service: TokenService = Depends(get_admin_token_service),
) -> OAuth2TokenResponse | JSONResponse:
    try:
        access_token, refresh_token = await token_service.refresh(data.refresh_token)
    except ValueError:
        return _oauth2_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="invalid_grant",
            error_description="非法的 refresh token",
        )
    except RuntimeError:
        return _oauth2_error(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error="server_error",
            error_description="Token解析异常",
        )
    return _build_token_response(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="用户登出")
async def logout(
    data: LogoutRequest,
    token_service: TokenService = Depends(get_admin_token_service),
    access_token: str | None = Depends(optional_oauth2_scheme),
) -> Response:
    with contextlib.suppress(ValueError):
        await token_service.revoke_refresh_token(data.refresh_token)
    if access_token:
        with contextlib.suppress(ValueError):
            await token_service.revoke_access_token(access_token)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
