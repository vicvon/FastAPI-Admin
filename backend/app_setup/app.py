from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app_setup.lifecycle import lifespan
from app_setup.permission_providers import init_permission_provider_bundle
from app_setup.router_registry import register_routers
from common.exceptions import AppError
from config.settings import get_settings
from core.handlers import (
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from core.logger import init_logging
from core.middleware import ContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    init_logging(
        level=settings.log.level,
        console_enabled=settings.log.console_enabled,
        file_enabled=settings.log.file_enabled,
        directory=settings.log.directory,
        filename=settings.log.filename,
        fmt=settings.log.format,
        debug=settings.debug,
        retention=settings.log.retention,
        rotation=settings.log.rotation,
        force=True,
    )
    if not settings.secret_key or len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY is required and must be at least 32 characters")
    allowed_algorithms = {"HS256", "RS256", "ES256"}
    if settings.algorithm not in allowed_algorithms:
        raise RuntimeError(f"Unsupported JWT algorithm: {settings.algorithm}")
    if settings.access_token_expire_minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ContextMiddleware)

    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    register_routers(app)
    init_permission_provider_bundle(app)
    return app
