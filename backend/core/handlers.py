import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.exceptions import AppError
from common.responses import ResponseSchema
from config.settings import get_settings
from core.context import RequestContext

logger = logging.getLogger(__name__)


def _safe_exception_summary(exc: Exception) -> str:
    if isinstance(exc, DBAPIError):
        orig = getattr(exc, "orig", None)
        if orig is not None:
            orig_text = str(orig).strip()
            if orig_text:
                return f"{type(orig).__name__}: {orig_text}"
            return type(orig).__name__
        return type(exc).__name__

    text = str(exc).strip()
    if text:
        return f"{type(exc).__name__}: {text}"
    return type(exc).__name__


async def app_exception_handler(_request: Request, exc: AppError):
    """处理自定义应用异常"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,  # 业务异常通常返回 200, 通过 code 区分
        content=ResponseSchema(
            code=exc.code, message=exc.message, data=exc.data
        ).model_dump(),
    )


async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    """处理 FastAPI/Starlette HTTP 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseSchema(
            code=exc.status_code, message=exc.detail, data=None
        ).model_dump(),
    )


async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """处理请求参数验证异常"""
    # 将验证错误详情转换为字符串或特定结构
    error_msg = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseSchema(
            code=422, message=f"Validation Error: {error_msg}", data=exc.errors()
        ).model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    """处理未捕获的全局异常"""
    logger.exception(
        "unhandled_exception request_id=%s path=%s",
        RequestContext.get_request_id(),
        getattr(request.url, "path", ""),
    )
    settings = get_settings()
    show_detail = bool(getattr(settings, "expose_error_detail", False))
    detail = _safe_exception_summary(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseSchema(
            code=500,
            message=detail if show_detail else "Internal Server Error",
            data=None,
        ).model_dump(),
    )
