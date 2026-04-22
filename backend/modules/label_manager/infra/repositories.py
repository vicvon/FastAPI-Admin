from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from modules.label_manager.domain.entities import Label
from modules.label_manager.domain.repositories import LabelRepositoryInterface


class LabelRepository(LabelRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: int) -> Label | None:
        statement = select(Label).where(
            Label.id == id,
            Label.namespace == "default",
            Label.deleted_at.is_(None),
        )
        result = await self._session.exec(statement)
        return result.first()

    async def list_labels(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
    ) -> Sequence[Label]:
        return await self.list_labels_with_scope(
            parent_id=parent_id,
            level=level,
            keyword=keyword,
            enabled=enabled,
            scope_filter=None,
        )

    async def list_labels_with_scope(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
        scope_filter=None,
    ) -> Sequence[Label]:
        statement = select(Label).where(
            Label.namespace == "default",
            Label.deleted_at.is_(None),
        )
        if scope_filter is not None:
            statement = statement.where(scope_filter)

        if parent_id is not None:
            statement = statement.where(Label.parent_id == parent_id)
        if level is not None:
            statement = statement.where(Label.level == level)
        if enabled is not None:
            statement = statement.where(Label.enabled == enabled)
        if keyword:
            statement = statement.where(
                or_(
                    Label.name.contains(keyword),
                    Label.description.contains(keyword),
                )
            )

        statement = statement.order_by(Label.sort_order.asc(), Label.id.asc())
        result = await self._session.exec(statement)
        return result.all()

    async def list_all(self, *, enabled: bool | None = None) -> Sequence[Label]:
        statement = select(Label).where(
            Label.namespace == "default",
            Label.deleted_at.is_(None),
        )
        if enabled is not None:
            statement = statement.where(Label.enabled == enabled)
        statement = statement.order_by(
            Label.level.asc(), Label.sort_order.asc(), Label.id.asc()
        )
        result = await self._session.exec(statement)
        return result.all()

    async def exists_same_name_under_parent(
        self,
        *,
        parent_id: int,
        name: str,
        exclude_id: int | None = None,
    ) -> bool:
        statement = select(Label).where(
            Label.namespace == "default",
            Label.deleted_at.is_(None),
            Label.parent_id == parent_id,
            Label.name == name,
        )
        if exclude_id is not None:
            statement = statement.where(Label.id != exclude_id)
        result = await self._session.exec(statement)
        return result.first() is not None

    async def count_children(self, *, parent_id: int) -> int:
        statement = (
            select(func.count())
            .select_from(Label)
            .where(
                Label.namespace == "default",
                Label.deleted_at.is_(None),
                Label.parent_id == parent_id,
            )
        )
        result = await self._session.exec(statement)
        return int(result.one() or 0)

    async def save(self, label: Label) -> Label:
        self._session.add(label)
        await self._session.commit()
        await self._session.refresh(label)
        return label

    async def update(self, label: Label) -> Label:
        self._session.add(label)
        await self._session.commit()
        await self._session.refresh(label)
        return label
