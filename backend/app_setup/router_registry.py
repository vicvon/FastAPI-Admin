from fastapi import FastAPI

from app_setup.module_registry import get_module_manifests
from common.responses import ResponseSchema


async def health_check() -> ResponseSchema[dict]:
    return ResponseSchema(data={"status": "ok"})


def register_routers(app: FastAPI) -> None:
    for manifest in get_module_manifests():
        if manifest.router is not None:
            app.include_router(manifest.router)
    app.add_api_route(
        "/health",
        health_check,
        methods=["GET"],
        response_model=ResponseSchema[dict],
        summary="服务状态检查",
    )
