from __future__ import annotations

from abc import ABC, abstractmethod

from common.auth import CurrentPrincipal


class ICurrentPrincipalResolver(ABC):
    """解析当前请求身份的共享接口。"""

    @abstractmethod
    async def resolve(self, token: str) -> CurrentPrincipal:
        raise NotImplementedError
