from __future__ import annotations

from common.exceptions import BusinessError
from common.ports import IPermissionChecker
from modules.iam.domain.rbac_service import RbacDomainService


class PermissionCheckerImpl(IPermissionChecker):
    """供业务模块使用的运行时权限检查实现。"""

    def __init__(self, rbac_service: RbacDomainService):
        self._rbac = rbac_service

    async def has_permission(self, user_id: int, resource: str, action: str) -> bool:
        return self._rbac.evaluate(f"user:{user_id}", resource, action)

    async def check_permission(self, user_id: int, resource: str, action: str) -> None:
        allowed = await self.has_permission(user_id, resource, action)
        if not allowed:
            raise BusinessError("Forbidden", code=403)
