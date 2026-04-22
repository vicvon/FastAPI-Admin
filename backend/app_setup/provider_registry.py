from __future__ import annotations

from fastapi import FastAPI

from app_setup.module_registry import get_module_manifests


def register_module_providers(app: FastAPI) -> None:
    for manifest in get_module_manifests():
        if manifest.provider_setup is not None:
            manifest.provider_setup(app)
