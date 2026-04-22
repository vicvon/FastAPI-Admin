from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IDataScopeResolver(ABC):
    """业务模块使用的数据权限解析接口。"""

    @abstractmethod
    async def resolve_scope(self, user_id: int, resource_type: str, action: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def build_query_scope(
        self,
        user_id: int,
        resource_type: str,
        action: str,
        model_cls: type[Any],
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def can_operate_entity(
        self,
        user_id: int,
        resource_type: str,
        action: str,
        entity: Any,
    ) -> bool:
        raise NotImplementedError
