from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import true


class ScopeHandler(ABC):
    @abstractmethod
    def build_query_filter(self, *, user_id: int, model_cls: Any):
        raise NotImplementedError

    @abstractmethod
    def can_operate_entity(self, *, user_id: int, entity: Any) -> bool:
        raise NotImplementedError


class AllScopeHandler(ScopeHandler):
    def build_query_filter(self, *, user_id: int, model_cls: Any):
        _ = (user_id, model_cls)
        return true()

    def can_operate_entity(self, *, user_id: int, entity: Any) -> bool:
        _ = (user_id, entity)
        return True


class SelfScopeHandler(ScopeHandler):
    def build_query_filter(self, *, user_id: int, model_cls: Any):
        owner_field = None
        if hasattr(model_cls, "owner_id"):
            owner_field = model_cls.owner_id
        elif hasattr(model_cls, "created_by"):
            owner_field = model_cls.created_by
        if owner_field is None:
            return true()
        return owner_field == int(user_id)

    def can_operate_entity(self, *, user_id: int, entity: Any) -> bool:
        owner_val = None
        if hasattr(entity, "owner_id"):
            owner_val = entity.owner_id
        elif hasattr(entity, "created_by"):
            owner_val = entity.created_by
        if owner_val is None:
            return False
        return int(owner_val) == int(user_id)


class ScopeHandlerRegistry:
    def __init__(self):
        self._handlers: dict[str, ScopeHandler] = {}

    def register(self, scope: str, handler: ScopeHandler) -> None:
        self._handlers[scope.upper()] = handler

    def get(self, scope: str) -> ScopeHandler:
        return self._handlers[scope.upper()]


def build_default_scope_handler_registry() -> ScopeHandlerRegistry:
    reg = ScopeHandlerRegistry()
    reg.register("ALL", AllScopeHandler())
    reg.register("SELF", SelfScopeHandler())
    return reg
