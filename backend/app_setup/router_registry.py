from fastapi import FastAPI

from common.responses import ResponseSchema
from modules.admin.api.v1.router import router as admin_router
from modules.label_manager.api.v1.router import router as label_manager_router


async def health_check() -> ResponseSchema[dict]:
    return ResponseSchema(data={"status": "ok"})


def register_routers(app: FastAPI) -> None:
    app.include_router(admin_router)
    app.include_router(label_manager_router)
    app.add_api_route(
        "/health",
        health_check,
        methods=["GET"],
        response_model=ResponseSchema[dict],
        summary="服务状态检查",
    )
