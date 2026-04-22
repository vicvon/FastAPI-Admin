from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CurrentPrincipal(BaseModel):
    """共享的当前登录主体, 供业务模块替代直接依赖 admin.User。"""

    model_config = ConfigDict(frozen=True)

    user_id: int
    username: str
    is_active: bool
    token_version: int

    @property
    def id(self) -> int:
        return self.user_id

    @property
    def subject(self) -> str:
        return f"user:{self.user_id}"
