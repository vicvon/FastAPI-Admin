from fastapi import FastAPI

from app_setup.module_registry import get_module_manifests


async def start_runtime_tasks(app: FastAPI) -> None:
    for manifest in get_module_manifests():
        for task in manifest.runtime_tasks:
            await task.startup(app)


async def stop_runtime_tasks(app: FastAPI) -> None:
    for manifest in reversed(get_module_manifests()):
        for task in reversed(manifest.runtime_tasks):
            await task.shutdown(app)
