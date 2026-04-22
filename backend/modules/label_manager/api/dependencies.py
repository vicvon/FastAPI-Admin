from __future__ import annotations

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app_setup.auth_dependencies import (
    get_current_principal,
    get_data_scope_resolver,
    require_permission,
)
from core.dependencies import get_db
from modules.label_manager.application.services import LabelService
from modules.label_manager.infra.repositories import LabelRepository


async def get_label_service(db: AsyncSession = Depends(get_db)) -> LabelService:
    repo = LabelRepository(db)
    return LabelService(repo)


__all__ = [
    "get_current_principal",
    "get_data_scope_resolver",
    "get_label_service",
    "require_permission",
]
