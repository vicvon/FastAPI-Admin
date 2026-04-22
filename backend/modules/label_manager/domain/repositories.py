from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from modules.label_manager.domain.entities import Label


class LabelRepositoryInterface(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Label | None:
        raise NotImplementedError

    @abstractmethod
    async def list_labels(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Label]:
        raise NotImplementedError

    @abstractmethod
    async def list_labels_with_scope(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
        scope_filter=None,
    ) -> Sequence[Label]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, *, enabled: bool | None = None) -> Sequence[Label]:
        raise NotImplementedError

    @abstractmethod
    async def exists_same_name_under_parent(
        self,
        *,
        parent_id: int,
        name: str,
        exclude_id: int | None = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def count_children(self, *, parent_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    async def save(self, label: Label) -> Label:
        raise NotImplementedError

    @abstractmethod
    async def update(self, label: Label) -> Label:
        raise NotImplementedError
