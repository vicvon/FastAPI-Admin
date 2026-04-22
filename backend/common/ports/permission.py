from __future__ import annotations

from abc import ABC, abstractmethod


class IPermissionChecker(ABC):
    """业务模块使用的只读权限检查接口。"""

    @abstractmethod
    async def has_permission(self, user_id: int, resource: str, action: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def check_permission(self, user_id: int, resource: str, action: str) -> None:
        raise NotImplementedError


class IPermissionManager(ABC):
    """admin 模块使用的权限投影与同步管理接口。"""

    @abstractmethod
    async def sync_role_policies(self, role_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def sync_user_roles(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def refresh_all(self) -> None:
        raise NotImplementedError
