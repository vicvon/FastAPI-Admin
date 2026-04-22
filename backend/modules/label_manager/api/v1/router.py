from fastapi import APIRouter

from modules.label_manager.api.v1 import labels

router = APIRouter(prefix="/api/v1")
router.include_router(labels.router)
