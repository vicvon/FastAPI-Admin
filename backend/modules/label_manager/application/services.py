from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from common.exceptions import BusinessError, NotFoundError
from modules.label_manager.domain.entities import Label
from modules.label_manager.domain.repositories import LabelRepositoryInterface
from utils.snowflake import next_snowflake_id


class LabelService:
    def __init__(self, repository: LabelRepositoryInterface):
        self._repository = repository

    async def list_labels(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
    ):
        return await self._repository.list_labels(
            parent_id=parent_id,
            level=level,
            keyword=keyword,
            enabled=enabled,
        )

    async def list_labels_with_scope(
        self,
        *,
        parent_id: int | None = None,
        level: int | None = None,
        keyword: str | None = None,
        enabled: bool | None = None,
        scope_filter=None,
    ):
        return await self._repository.list_labels_with_scope(
            parent_id=parent_id,
            level=level,
            keyword=keyword,
            enabled=enabled,
            scope_filter=scope_filter,
        )

    async def list_tree(self, *, enabled: bool | None = None) -> list[dict[str, Any]]:
        labels = await self._repository.list_all(enabled=enabled)
        nodes: dict[int, dict[str, Any]] = {}
        children_map: dict[int, list[int]] = defaultdict(list)
        roots: list[int] = []

        for label in labels:
            nodes[label.id] = {
                "id": str(label.id),
                "name": label.name,
                "level": label.level,
                "parent_id": str(label.parent_id),
                "root_id": str(label.root_id),
                "path": label.path,
                "sort_order": label.sort_order,
                "enabled": label.enabled,
                "description": label.description,
                "created_at": label.created_at,
                "updated_at": label.updated_at,
                "children": [],
            }
            if label.parent_id == 0:
                roots.append(label.id)
            else:
                children_map[label.parent_id].append(label.id)

        for parent_id, child_ids in children_map.items():
            parent = nodes.get(parent_id)
            if parent is None:
                continue
            parent["children"] = [nodes[cid] for cid in child_ids if cid in nodes]

        return [nodes[rid] for rid in roots if rid in nodes]

    async def get_by_id(self, id: int) -> Label | None:
        return await self._repository.get_by_id(id)

    async def resolve_full_names(self, *, label_ids: list[int]) -> dict[int, str]:
        if not label_ids:
            return {}

        labels = await self._repository.list_all(enabled=None)
        by_id: dict[int, Label] = {int(label.id): label for label in labels}

        result: dict[int, str] = {}
        for lid in label_ids:
            node = by_id.get(int(lid))
            if node is None:
                continue
            names: list[str] = []
            current = node
            for _ in range(3):
                names.append(current.name)
                if int(current.parent_id) == 0:
                    break
                parent = by_id.get(int(current.parent_id))
                if parent is None:
                    break
                current = parent
            names.reverse()
            result[int(lid)] = ":".join([n for n in names if n])

        return result

    async def create(
        self,
        *,
        name: str,
        parent_id: int,
        sort_order: int,
        enabled: bool,
        description: str | None,
        operator_id: int,
    ) -> Label:
        parent = None
        if parent_id != 0:
            parent = await self._repository.get_by_id(parent_id)
            if parent is None:
                raise NotFoundError(f"父标签不存在: {parent_id}")

        level = 1 if parent is None else parent.level + 1
        if level < 1 or level > 3:
            raise BusinessError("标签层级只允许 1~3 级")

        if await self._repository.exists_same_name_under_parent(
            parent_id=parent_id, name=name
        ):
            raise BusinessError(f"同级标签名称已存在: {name}")

        new_id = next_snowflake_id()
        if parent is None:
            root_id = new_id
            path = f"/{new_id}"
        elif level == 2:
            root_id = parent.id
            path = f"/{root_id}/{new_id}"
        else:
            root_id = parent.root_id
            path = f"/{root_id}/{parent.id}/{new_id}"

        label = Label(
            id=new_id,
            namespace="default",
            name=name,
            level=level,
            parent_id=parent_id,
            root_id=root_id,
            path=path,
            sort_order=sort_order,
            enabled=enabled,
            description=description,
            created_by=operator_id,
            updated_by=None,
            created_at=datetime.now(UTC).astimezone(),
            updated_at=datetime.now(UTC).astimezone(),
            deleted_at=None,
        )
        return await self._repository.save(label)

    async def update(
        self,
        *,
        id: int,
        name: str | None,
        sort_order: int | None,
        enabled: bool | None,
        description: str | None,
        operator_id: int,
    ) -> Label:
        label = await self._repository.get_by_id(id)
        if label is None:
            raise NotFoundError(f"标签不存在: {id}")

        if name is not None and name != label.name:
            if await self._repository.exists_same_name_under_parent(
                parent_id=label.parent_id, name=name, exclude_id=label.id
            ):
                raise BusinessError(f"同级标签名称已存在: {name}")
            label.name = name

        if sort_order is not None:
            label.sort_order = sort_order
        if enabled is not None:
            label.enabled = enabled
        if description is not None:
            label.description = description

        label.updated_by = operator_id
        label.updated_at = datetime.now(UTC).astimezone()
        return await self._repository.update(label)

    async def set_enabled(self, *, id: int, enabled: bool, operator_id: int) -> Label:
        return await self.update(
            id=id,
            name=None,
            sort_order=None,
            enabled=enabled,
            description=None,
            operator_id=operator_id,
        )

    async def move(self, *, id: int, new_parent_id: int, operator_id: int) -> Label:
        label = await self._repository.get_by_id(id)
        if label is None:
            raise NotFoundError(f"标签不存在: {id}")

        if label.parent_id == new_parent_id:
            return label

        new_parent = None
        if new_parent_id != 0:
            new_parent = await self._repository.get_by_id(new_parent_id)
            if new_parent is None:
                raise NotFoundError(f"新父标签不存在: {new_parent_id}")

        if label.level == 1 and new_parent_id != 0:
            raise BusinessError("一级标签不允许移动到父节点下")
        if label.level == 2 and (new_parent is None or new_parent.level != 1):
            raise BusinessError("二级标签只能移动到一级标签下")
        if label.level == 3 and (new_parent is None or new_parent.level != 2):
            raise BusinessError("三级标签只能移动到二级标签下")

        if await self._repository.exists_same_name_under_parent(
            parent_id=new_parent_id, name=label.name, exclude_id=label.id
        ):
            raise BusinessError(f"同级标签名称已存在: {label.name}")

        label.parent_id = new_parent_id

        if label.level == 1:
            label.root_id = label.id
            label.path = f"/{label.id}"
        elif label.level == 2:
            label.root_id = int(new_parent.id) if new_parent is not None else 0
            label.path = f"/{label.root_id}/{label.id}"
        else:
            label.root_id = int(new_parent.root_id) if new_parent is not None else 0
            label.path = f"/{label.root_id}/{new_parent.id}/{label.id}"

        label.updated_by = operator_id
        label.updated_at = datetime.now(UTC).astimezone()

        saved = await self._repository.update(label)

        if label.level == 2:
            children = await self._repository.list_labels(parent_id=label.id, level=3)
            for child in children:
                child.root_id = saved.root_id
                child.path = f"/{saved.root_id}/{saved.id}/{child.id}"
                child.updated_by = operator_id
                child.updated_at = datetime.now(UTC).astimezone()
                await self._repository.update(child)

        if label.level == 1:
            level2_children = await self._repository.list_labels(
                parent_id=label.id, level=2
            )
            for level2 in level2_children:
                level2.root_id = saved.id
                level2.path = f"/{saved.id}/{level2.id}"
                level2.updated_by = operator_id
                level2.updated_at = datetime.now(UTC).astimezone()
                await self._repository.update(level2)
                level3_children = await self._repository.list_labels(
                    parent_id=level2.id, level=3
                )
                for level3 in level3_children:
                    level3.root_id = saved.id
                    level3.path = f"/{saved.id}/{level2.id}/{level3.id}"
                    level3.updated_by = operator_id
                    level3.updated_at = datetime.now(UTC).astimezone()
                    await self._repository.update(level3)

        return saved

    async def delete(self, *, id: int, operator_id: int) -> None:
        label = await self._repository.get_by_id(id)
        if label is None:
            raise NotFoundError(f"标签不存在: {id}")

        children_count = await self._repository.count_children(parent_id=label.id)
        if children_count > 0:
            raise BusinessError("存在子标签, 无法删除")

        label.deleted_at = datetime.now(UTC).astimezone()
        label.updated_by = operator_id
        label.updated_at = datetime.now(UTC).astimezone()
        await self._repository.update(label)
