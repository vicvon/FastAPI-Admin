from __future__ import annotations

from fastapi import FastAPI

__all__ = ["create_app"]


def create_app() -> FastAPI:
    from app_setup.app import create_app as _create_app

    return _create_app()
