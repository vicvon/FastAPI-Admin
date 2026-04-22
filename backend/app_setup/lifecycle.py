from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app_setup.permission_providers import shutdown_permission_runtime
from app_setup.task_registry import start_runtime_tasks, stop_runtime_tasks
from core.cache import cache
from core.logger import get_logger

logger = get_logger(__name__)


def list_all_apis(app: FastAPI) -> None:
    for route in app.routes:
        if isinstance(route, APIRoute):
            path = route.path
            if path.startswith(("/openapi.json", "/docs", "/redoc")):
                continue

            summary = route.summary
            for method in route.methods:
                logger.debug(f"{summary}: {method.upper()}: {path}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    list_all_apis(app)
    await start_runtime_tasks(app)
    yield
    await stop_runtime_tasks(app)

    try:
        shutdown_permission_runtime(app)
    except Exception:
        logger.opt(exception=True).warning("shutdown casbin watcher failed")

    if cache._initialized:
        await cache.close()
