from fastapi import APIRouter

from modules.admin.api.v1 import auth, permissions, roles, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(permissions.router)
router.include_router(roles.router)
router.include_router(users.router)
