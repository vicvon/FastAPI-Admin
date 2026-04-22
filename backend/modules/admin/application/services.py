import asyncio
import hashlib
import json
import time
from collections import deque
from collections.abc import Sequence
from typing import Any

from sqlmodel import select

from common.ports import IPermissionManager
from core.cache import cache
from core.logger import get_logger
from core.redis_lock import redis_lock
from core.security import get_password_hash, verify_password
from modules.admin.application.contracts import (
    DataScopeRuleUpsert,
    RoleCreate,
    RoleGrantResponse,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from modules.admin.application.dto import (
    GlobalApiPermissionListDTO,
    GlobalDataScopeListDTO,
    GlobalDataScopeOptionDTO,
    GlobalMenuPermissionListDTO,
    RoleApiGroupDTO,
    RoleApiPermissionDTO,
    RoleApiPermissionListDTO,
    RoleDataScopeGroupDTO,
    RoleDataScopeListDTO,
    RoleDataScopeRuleDTO,
    RoleMenuItemDTO,
)
from modules.admin.domain.entities import (
    DataScope,
    MenuPermission,
    PermissionType,
    Role,
    RoleDataScopeRule,
    RoleGrantJob,
    RoleGrantJobStatus,
    User,
)
from modules.admin.domain.repositories import (
    PermissionRepository,
    RoleGrantJobRepository,
    RoleRepository,
    ScopeRuleRepository,
    UserRepository,
)
from modules.admin.domain.role_code import build_role_code

logger = get_logger(__name__)
USER_ROLE_SYNC_RETRY_ZSET_KEY = "admin:user_role_sync_retry:zset"
USER_ROLE_SYNC_RETRY_COUNT_HASH_KEY = "admin:user_role_sync_retry:count"
USER_ROLE_SYNC_RETRY_MAX_RETRIES = 8


def _user_role_retry_delay_seconds(retry_count: int) -> int:
    # 1, 2, 4, 8 ... capped to 30s
    return min(2 ** max(retry_count, 0), 30)


async def enqueue_user_role_sync_retry(
    *, user_id: int, delay_seconds: int = 1, retry_count: int = 0
) -> bool:
    try:
        due_at = time.time() + max(delay_seconds, 0)
        zset_key = cache.make_key(USER_ROLE_SYNC_RETRY_ZSET_KEY)
        retry_key = cache.make_key(USER_ROLE_SYNC_RETRY_COUNT_HASH_KEY)
        member = str(int(user_id))
        await cache.client.zadd(zset_key, {member: due_at})
        await cache.client.hset(retry_key, member, str(max(retry_count, 0)))
        return True
    except Exception:
        logger.opt(exception=True).error(
            "admin.user_role_retry_enqueue_failed user_id={}", user_id
        )
        return False


async def clear_user_role_sync_retry(*, user_id: int) -> None:
    zset_key = cache.make_key(USER_ROLE_SYNC_RETRY_ZSET_KEY)
    retry_key = cache.make_key(USER_ROLE_SYNC_RETRY_COUNT_HASH_KEY)
    member = str(int(user_id))
    try:
        await cache.client.zrem(zset_key, member)
        await cache.client.hdel(retry_key, member)
    except Exception:
        logger.opt(exception=True).warning(
            "admin.user_role_retry_clear_failed user_id={}", user_id
        )


async def retry_due_user_role_groupings(
    permission_manager: IPermissionManager,
    *,
    limit: int = 100,
) -> tuple[int, int]:
    attempted = 0
    succeeded = 0
    zset_key = cache.make_key(USER_ROLE_SYNC_RETRY_ZSET_KEY)
    retry_key = cache.make_key(USER_ROLE_SYNC_RETRY_COUNT_HASH_KEY)
    now_ts = time.time()
    due_members = await cache.client.zrangebyscore(
        zset_key, min="-inf", max=now_ts, start=0, num=limit
    )
    for member in due_members:
        try:
            user_id = int(member)
        except Exception:
            await cache.client.zrem(zset_key, member)
            await cache.client.hdel(retry_key, member)
            continue
        attempted += 1
        try:
            await permission_manager.sync_user_roles(user_id)
            await clear_user_role_sync_retry(user_id=user_id)
            succeeded += 1
        except Exception as exc:
            retry_raw = await cache.client.hget(retry_key, member)
            retry_count = int(retry_raw) if retry_raw is not None else 0
            next_retry = retry_count + 1
            if next_retry > USER_ROLE_SYNC_RETRY_MAX_RETRIES:
                await cache.client.zrem(zset_key, member)
                await cache.client.hdel(retry_key, member)
                logger.opt(exception=True).error(
                    "admin.user_role_retry_exhausted user_id={} retries={} error={}",
                    user_id,
                    next_retry,
                    str(exc),
                )
                continue
            delay_seconds = _user_role_retry_delay_seconds(next_retry)
            await cache.client.hset(retry_key, member, str(next_retry))
            await cache.client.zadd(zset_key, {member: time.time() + delay_seconds})
            logger.opt(exception=True).warning(
                "admin.user_role_retry_failed user_id={} retries={} next_delay={} error={}",
                user_id,
                next_retry,
                delay_seconds,
                str(exc),
            )
    return attempted, succeeded


def _expand_menu_with_ancestors(
    seed_menu_ids: set[int], menu_lookup: dict[int, Any]
) -> set[int]:
    visible_ids = set(seed_menu_ids)
    for menu_id in list(seed_menu_ids):
        current_id = menu_id
        visited: set[int] = set()
        while current_id is not None:
            current = menu_lookup.get(current_id)
            if current is None:
                break
            parent_id = current.parent_id
            if parent_id is None or parent_id in visited:
                break
            visited.add(parent_id)
            if parent_id in menu_lookup:
                visible_ids.add(parent_id)
            current_id = parent_id
    return visible_ids


def _build_menu_tree_from_ids(
    menu_ids: set[int], menu_lookup: dict[int, Any], stringify_ids: bool = False
) -> list[dict]:
    nodes: list[dict] = []
    for menu_id in menu_ids:
        menu = menu_lookup.get(menu_id)
        if menu is None or menu.id is None:
            continue
        nodes.append(
            {
                "id": menu.id,
                "name": menu.name,
                "parent_id": menu.parent_id,
                "path": menu.path,
                "icon": menu.icon,
                "component": menu.component,
                "sort_order": menu.sort_order,
                "status": menu.status,
                "children": [],
            }
        )

    lookup = {node["id"]: node for node in nodes if node["id"] is not None}
    roots: list[dict] = []
    for node in nodes:
        parent_id = node["parent_id"]
        if parent_id is not None and parent_id in lookup:
            lookup[parent_id]["children"].append(node)
        else:
            roots.append(node)

    def sort_tree(tree_nodes: list[dict]) -> None:
        tree_nodes.sort(key=lambda x: (x.get("sort_order", 0), int(x.get("id", 0))))
        for item in tree_nodes:
            sort_tree(item["children"])

    def stringify_tree(tree_nodes: list[dict]) -> None:
        for item in tree_nodes:
            if item.get("id") is not None:
                item["id"] = str(item["id"])
            if item.get("parent_id") is not None:
                item["parent_id"] = str(item["parent_id"])
            stringify_tree(item["children"])

    sort_tree(roots)
    if stringify_ids:
        stringify_tree(roots)
    return roots


class PermissionService:
    def __init__(self, permissions: PermissionRepository) -> None:
        self.permissions = permissions

    async def get_global_menu_permissions(self) -> GlobalMenuPermissionListDTO:
        menus = await self.permissions.list_menu_permissions()
        menu_nodes = []
        for menu in menus:
            menu_nodes.append(
                {
                    "id": menu.id,
                    "name": menu.name,
                    "parent_id": menu.parent_id,
                    "path": menu.path,
                    "component": menu.component,
                    "icon": menu.icon,
                    "sort_order": menu.sort_order,
                    "status": menu.status,
                    "children": [],
                }
            )
        menu_lookup = {
            item["id"]: item for item in menu_nodes if item["id"] is not None
        }
        menu_roots: list[dict] = []
        for item in menu_nodes:
            parent_id = item["parent_id"]
            if parent_id is not None and parent_id in menu_lookup:
                menu_lookup[parent_id]["children"].append(item)
            else:
                menu_roots.append(item)

        def sort_menu_tree(nodes: list[dict]) -> None:
            nodes.sort(key=lambda x: (x.get("sort_order", 0), int(x.get("id", 0))))
            for node in nodes:
                sort_menu_tree(node["children"])

        def to_menu_item(node: dict) -> RoleMenuItemDTO:
            return RoleMenuItemDTO(
                id=int(node["id"]),
                name=node["name"],
                parent_id=node["parent_id"],
                path=node["path"],
                component=node["component"],
                icon=node["icon"],
                sort_order=node["sort_order"],
                status=node["status"],
                children=[to_menu_item(child) for child in node["children"]],
            )

        sort_menu_tree(menu_roots)
        return GlobalMenuPermissionListDTO(
            menus=[to_menu_item(node) for node in menu_roots]
        )

    async def get_global_api_permissions(self) -> GlobalApiPermissionListDTO:
        api_permissions = await self.permissions.list_api_permissions()
        grouped_api_permissions: dict[str, list[RoleApiPermissionDTO]] = {}
        sorted_api_permissions = sorted(
            [item for item in api_permissions if item.id is not None],
            key=lambda x: (
                x.group_name or "default",
                x.method,
                x.api_path,
                int(x.id or 0),
            ),
        )
        for item in sorted_api_permissions:
            group_name = item.group_name or "default"
            grouped_api_permissions.setdefault(group_name, []).append(
                RoleApiPermissionDTO(
                    id=item.id,
                    name=item.name,
                    api_path=item.api_path,
                    method=item.method,
                    status=item.status,
                )
            )
        api_groups = [
            RoleApiGroupDTO(group_name=group_name, permissions=permissions)
            for group_name, permissions in sorted(grouped_api_permissions.items())
        ]
        return GlobalApiPermissionListDTO(api_groups=api_groups)

    async def get_global_data_scope_options(self) -> GlobalDataScopeListDTO:
        # 当前只考虑resource_type=__all__, DataScope为ALL和SELF的情况
        # TODO 未来丰富数据权限, 更细粒度的控制
        resource_types = ["__all__"]
        data_scope_options = [
            GlobalDataScopeOptionDTO(scope=scope, resource_types=resource_types)
            for scope in [DataScope.ALL, DataScope.SELF]
        ]
        return GlobalDataScopeListDTO(data_scope_options=data_scope_options)

    async def create_menu_permission(
        self,
        *,
        name: str,
        parent_id: int | None,
        path: str | None,
        component: str | None,
        icon: str | None,
        sort_order: int,
        status: str,
    ) -> MenuPermission:
        if parent_id is not None:
            parent = await self.permissions.get_menu_permission(parent_id)
            if parent is None:
                raise ValueError("父级菜单不存在")
        menu = MenuPermission(
            name=name,
            parent_id=parent_id,
            path=path,
            component=component,
            icon=icon,
            sort_order=sort_order,
            status=status,
        )
        return await self.permissions.create_menu_permission(menu)

    async def update_menu_permission(
        self,
        *,
        menu_id: int,
        name: str,
        parent_id: int | None,
        path: str | None,
        component: str | None,
        icon: str | None,
        sort_order: int,
        status: str,
    ) -> MenuPermission:
        menu = await self.permissions.get_menu_permission(menu_id)
        if menu is None:
            raise ValueError("菜单不存在")
        if parent_id == menu_id:
            raise ValueError("父级菜单不能为自身")
        if parent_id is not None:
            parent = await self.permissions.get_menu_permission(parent_id)
            if parent is None:
                raise ValueError("父级菜单不存在")
        menu.name = name
        menu.parent_id = parent_id
        menu.path = path
        menu.component = component
        menu.icon = icon
        menu.sort_order = sort_order
        menu.status = status
        return await self.permissions.update_menu_permission(menu)

    async def delete_menu_permission(self, menu_id: int) -> None:
        menu = await self.permissions.get_menu_permission(menu_id)
        if menu is None:
            raise ValueError("菜单不存在")
        menus = await self.permissions.list_menu_permissions()
        if any(item.parent_id == menu_id for item in menus):
            raise ValueError("请先删除子菜单")
        await self.permissions.delete_menu_permission(menu_id)


class RoleService:
    def __init__(
        self,
        roles: RoleRepository,
        permissions: PermissionRepository,
        permission_manager: IPermissionManager | None = None,
    ) -> None:
        self.roles = roles
        self.permissions = permissions
        self.permission_manager = permission_manager

    async def list_roles(self) -> Sequence[Role]:
        return await self.roles.list()

    async def is_protected_role(self, role: Role) -> bool:
        from modules.admin.domain.system_semantics import is_protected_role

        return is_protected_role(role)

    async def get_permission_ids(self, role_id: int) -> list[int]:
        return await self.roles.get_permission_ids(role_id)

    async def get_parent_role_id(self, role_id: int) -> int | None:
        return await self.roles.get_parent_role_id(role_id)

    async def create_role(self, data: RoleCreate) -> Role:
        parent_role_id = data.parent_role_id
        if parent_role_id is not None:
            parent = await self.roles.get(parent_role_id)
            if parent is None:
                raise ValueError("上级角色不存在")

        role = Role(name=data.name, code="", parent_role_id=parent_role_id)
        role.code = build_role_code(role.name, role.id)
        role = await self.roles.create(role)

        if role.id is None:
            raise ValueError("角色创建失败")

        if self.permission_manager is None:
            raise RuntimeError("Permission manager is not configured")
        await self.permission_manager.sync_role_policies(role.id)
        return role

    async def update_role(self, role_id: int, data: RoleUpdate) -> Role | None:
        role = await self.roles.get(role_id)
        if role is None:
            return None

        role.name = data.name
        role = await self.roles.update(role)
        return role

    async def _get_child_role_ids(self, parent_role_id: int) -> list[int]:
        from sqlmodel import select

        from modules.admin.domain.entities import Role

        statement = select(Role.id).where(Role.parent_role_id == parent_role_id)
        result = await self.roles.session.exec(statement)
        child_ids: list[int] = []
        for row in result.all():
            cid = row[0] if isinstance(row, (tuple, list)) else row
            if cid is not None:
                child_ids.append(int(cid))
        return child_ids

    async def _get_descendant_role_ids(self, role_id: int) -> list[int]:
        descendants: list[int] = []
        queue: deque[int] = deque([role_id])
        visited: set[int] = {role_id}
        while queue:
            current_id = queue.popleft()
            child_ids = await self._get_child_role_ids(current_id)
            for child_id in child_ids:
                if child_id in visited:
                    continue
                visited.add(child_id)
                descendants.append(child_id)
                queue.append(child_id)
        return descendants

    async def get_role_menu_ids(self, role_id: int) -> list[int]:
        role = await self.roles.get(role_id)
        if role is None:
            raise ValueError("角色不存在")
        return await self.roles.get_permission_ids_by_type(role_id, PermissionType.MENU)

    async def get_role_menu_detail_tree(self, role_id: int) -> list[dict]:
        role = await self.roles.get(role_id)
        if role is None:
            raise ValueError("角色不存在")
        selected_ids = set(
            await self.roles.get_permission_ids_by_type(role_id, PermissionType.MENU)
        )
        if not selected_ids:
            return []
        all_menus = await self.permissions.list_menu_permissions()
        menu_lookup = {menu.id: menu for menu in all_menus if menu.id is not None}
        visible_ids = _expand_menu_with_ancestors(selected_ids, menu_lookup)
        return _build_menu_tree_from_ids(visible_ids, menu_lookup, stringify_ids=False)

    async def set_role_menu_ids(
        self, role_id: int, menu_ids: list[int], include_ancestors: bool = True
    ) -> None:
        role = await self.roles.get(role_id)
        if role is None:
            raise ValueError("角色不存在")

        target_ids = {int(v) for v in menu_ids}
        if not target_ids:
            await self.roles.set_permission_ids_by_type(
                role_id, PermissionType.MENU, []
            )
            return

        permissions = await self.permissions.get_menu_permissions_by_ids(
            list(target_ids)
        )
        found_ids = {p.id for p in permissions if p.id is not None}
        missing_ids = target_ids - found_ids
        if missing_ids:
            raise ValueError("部分菜单不存在")

        final_ids = set(found_ids)

        if include_ancestors:
            all_perms = await self.permissions.list_menu_permissions()
            parent_map = {p.id: p.parent_id for p in all_perms if p.id is not None}
            for menu_id in list(final_ids):
                current_id = menu_id
                visited: set[int] = set()
                while True:
                    parent_id = parent_map.get(current_id)
                    if parent_id is None:
                        break
                    if parent_id in visited:
                        break
                    visited.add(parent_id)
                    final_ids.add(parent_id)
                    current_id = parent_id

        parent_role_id = await self.roles.get_parent_role_id(role_id)
        if parent_role_id is not None:
            # 菜单权限子集校验: 子角色最终菜单集合必须是父角色菜单集合的子集
            allowed_ids = set(
                await self.roles.get_permission_ids_by_type(
                    parent_role_id, PermissionType.MENU
                )
            )
            if include_ancestors and allowed_ids:
                all_perms = await self.permissions.list_menu_permissions()
                parent_map = {p.id: p.parent_id for p in all_perms if p.id is not None}
                for menu_id in list(allowed_ids):
                    current_id = menu_id
                    visited: set[int] = set()
                    while True:
                        parent_id = parent_map.get(current_id)
                        if parent_id is None:
                            break
                        if parent_id in visited:
                            break
                        visited.add(parent_id)
                        allowed_ids.add(parent_id)
                        current_id = parent_id
            if not final_ids.issubset(allowed_ids):
                raise ValueError("角色菜单权限不允许超过上级角色菜单权限")

        current_ids = set(
            await self.roles.get_permission_ids_by_type(role_id, PermissionType.MENU)
        )
        removed_ids = current_ids - final_ids
        if removed_ids:
            descendants = await self._get_descendant_role_ids(role_id)
            for descendant_id in descendants:
                descendant_ids = set(
                    await self.roles.get_permission_ids_by_type(
                        descendant_id, PermissionType.MENU
                    )
                )
                if descendant_ids & removed_ids:
                    raise ValueError("取消权限前先取消下级角色权限")

        await self.roles.set_permission_ids_by_type(
            role_id, PermissionType.MENU, sorted(final_ids)
        )


class RolePermissionApplicationService:
    def __init__(
        self,
        roles: RoleRepository,
        permissions: PermissionRepository,
        scope_rules: ScopeRuleRepository,
        grant_jobs: RoleGrantJobRepository,
        permission_manager: IPermissionManager | None = None,
    ) -> None:
        self.roles = roles
        self.permissions = permissions
        self.scope_rules = scope_rules
        self.grant_jobs = grant_jobs
        self.permission_manager = permission_manager

    async def grant_api_permissions(
        self,
        *,
        role_id: int,
        api_permission_ids: list[int],
        operator_id: int,
    ) -> RoleGrantResponse:
        role = await self.roles.get(role_id)
        if role is None or role.id is None:
            raise ValueError("角色不存在")

        lock_key = f"admin:role_grant:api:{role_id}"
        async with redis_lock(key=lock_key, ttl_seconds=30) as got_lock:
            if not got_lock:
                raise RuntimeError("角色接口权限处理中")

            normalized_permission_ids = self._normalize_api_permission_ids(
                api_permission_ids
            )
            fingerprint = self._calc_api_fingerprint(
                role_id=role_id, api_permission_ids=normalized_permission_ids
            )
            last_job = await self.grant_jobs.find_latest_by_role_id(role_id)
            if last_job is not None and last_job.request_id == fingerprint:
                if (
                    last_job.status == RoleGrantJobStatus.SYNC_FAILED
                    and last_job.id is not None
                ):
                    retried = await self.retry_failed_grant_job(last_job.id)
                    return RoleGrantResponse(
                        role_id=last_job.role_id,
                        dimension="api",
                        synced=retried.synced,
                        skipped=False,
                    )
                return RoleGrantResponse(
                    role_id=last_job.role_id,
                    dimension="api",
                    synced=last_job.synced,
                    skipped=True,
                )

            job = await self.grant_jobs.create(
                RoleGrantJob(
                    role_id=role_id,
                    request_id=fingerprint,
                    api_permission_ids=normalized_permission_ids,
                    data_scope_rules=[],
                    operator_id=operator_id,
                    status=RoleGrantJobStatus.APPLYING,
                    synced=False,
                )
            )
            try:
                await self._apply_api_permissions(
                    role_id=role_id,
                    api_permission_ids=normalized_permission_ids,
                    operator_id=operator_id,
                    fingerprint=fingerprint,
                )
            except Exception as exc:
                job.status = RoleGrantJobStatus.SYNC_FAILED
                job.synced = False
                job.last_error = str(exc)
                await self.grant_jobs.update(job)
                raise
            try:
                if self.permission_manager is None:
                    raise RuntimeError("Permission manager is not configured")
                await self.permission_manager.sync_role_policies(role_id)
                job.status = RoleGrantJobStatus.SYNCED
                job.synced = True
                job.last_error = None
                await self.grant_jobs.update(job)
            except Exception as exc:
                job.status = RoleGrantJobStatus.SYNC_FAILED
                job.synced = False
                job.last_error = str(exc)
                await self.grant_jobs.update(job)

            return RoleGrantResponse(
                role_id=role_id,
                dimension="api",
                synced=job.synced,
                skipped=False,
            )

    async def grant_data_scopes(
        self,
        *,
        role_id: int,
        data_scope_rules: list[DataScopeRuleUpsert],
        operator_id: int,
    ) -> RoleGrantResponse:
        role = await self.roles.get(role_id)
        if role is None or role.id is None:
            raise ValueError("角色不存在")

        lock_key = f"admin:role_grant:scope:{role_id}"
        async with redis_lock(key=lock_key, ttl_seconds=30) as got_lock:
            if not got_lock:
                raise RuntimeError("角色接口权限处理中")

            normalized_scope_rules = self._normalize_scope_rules(data_scope_rules)
            fingerprint = self._calc_scope_fingerprint(
                role_id=role_id, data_scope_rules=normalized_scope_rules
            )
            current_scope_rules = await self.scope_rules.list_role_scope_rules(role_id)
            current_normalized_scope_rules = self._normalize_scope_rules(
                [
                    DataScopeRuleUpsert(
                        resource_type=rule.resource_type,
                        view_scope=rule.view_scope,
                        edit_scope=rule.edit_scope,
                        custom_rule_id=rule.custom_rule_id,
                    )
                    for rule in current_scope_rules
                ]
            )
            current_fingerprint = self._calc_scope_fingerprint(
                role_id=role_id, data_scope_rules=current_normalized_scope_rules
            )
            if current_fingerprint == fingerprint:
                return RoleGrantResponse(
                    role_id=role_id,
                    dimension="scope",
                    synced=None,
                    skipped=True,
                )

            scope_rule_entities = self._build_scope_rule_entities(
                role_id=role_id, data_scope_rules=normalized_scope_rules
            )
            try:
                await self.scope_rules.replace_role_data_scope_rules(
                    role_id=role_id, rules=scope_rule_entities, auto_commit=False
                )
                await self.roles.session.commit()
            except Exception:
                await self.roles.session.rollback()
                raise
            logger.info(
                "admin.role_scope_grant_applied role_id={} fingerprint={} operator_id={} scope_rule_count={}",
                role_id,
                fingerprint,
                operator_id,
                len(scope_rule_entities),
            )
            return RoleGrantResponse(
                role_id=role_id,
                dimension="scope",
                synced=None,
                skipped=False,
            )

    async def get_role_api_permissions(self, role_id: int) -> RoleApiPermissionListDTO:
        role = await self.roles.get(role_id)
        if role is None or role.id is None:
            raise ValueError("角色不存在")
        api_permission_ids = await self.roles.get_permission_ids_by_type(
            role_id, PermissionType.API
        )
        api_permissions = await self.permissions.get_api_permissions_by_ids(
            api_permission_ids
        )
        grouped_permissions: dict[str, list[RoleApiPermissionDTO]] = {}
        sorted_api_permissions = sorted(
            [p for p in api_permissions if p.id is not None],
            key=lambda x: (
                x.group_name or "default",
                x.method,
                x.api_path,
                int(x.id or 0),
            ),
        )
        for permission in sorted_api_permissions:
            group_name = permission.group_name or "default"
            grouped_permissions.setdefault(group_name, []).append(
                RoleApiPermissionDTO(
                    id=permission.id,
                    name=permission.name,
                    api_path=permission.api_path,
                    method=permission.method,
                    status=permission.status,
                )
            )
        api_groups = [
            RoleApiGroupDTO(group_name=group_name, permissions=permissions)
            for group_name, permissions in sorted(grouped_permissions.items())
        ]
        return RoleApiPermissionListDTO(role_id=role.id, api_groups=api_groups)

    async def get_role_data_scopes(self, role_id: int) -> RoleDataScopeListDTO:
        role = await self.roles.get(role_id)
        if role is None or role.id is None:
            raise ValueError("角色不存在")
        role_scope_rules = await self.scope_rules.list_role_scope_rules(role_id)
        grouped_scope_rules: dict[
            tuple[DataScope, DataScope], list[RoleDataScopeRuleDTO]
        ] = {}
        for rule in role_scope_rules:
            grouped_scope_rules.setdefault(
                (rule.view_scope, rule.edit_scope), []
            ).append(
                RoleDataScopeRuleDTO(
                    resource_type=rule.resource_type,
                    custom_rule_id=rule.custom_rule_id,
                )
            )
        data_scope_groups: list[RoleDataScopeGroupDTO] = []
        for (view_scope, edit_scope), rules in grouped_scope_rules.items():
            sorted_rules = sorted(rules, key=lambda x: x.resource_type)
            data_scope_groups.append(
                RoleDataScopeGroupDTO(
                    view_scope=view_scope,
                    edit_scope=edit_scope,
                    rules=sorted_rules,
                )
            )
        data_scope_groups.sort(key=lambda x: (x.view_scope.value, x.edit_scope.value))
        return RoleDataScopeListDTO(
            role_id=role.id, data_scope_groups=data_scope_groups
        )

    async def retry_failed_grant_job(self, job_id: int) -> RoleGrantResponse:
        job = await self.grant_jobs.get(job_id)
        if job is None:
            raise ValueError("Grant job not found")
        if job.status != RoleGrantJobStatus.SYNC_FAILED:
            return RoleGrantResponse(
                role_id=job.role_id, dimension="api", synced=job.synced
            )
        latest = await self.grant_jobs.find_latest_by_role_id(job.role_id)
        if latest is not None and latest.id != job.id:
            job.status = RoleGrantJobStatus.SYNCED
            job.synced = True
            job.last_error = (
                None if latest.id is None else f"SUPERSEDED_BY_NEWER_JOB:{latest.id}"
            )
            await self.grant_jobs.update(job)
            return RoleGrantResponse(role_id=job.role_id, dimension="api", synced=True)
        try:
            if self.permission_manager is None:
                raise RuntimeError("Permission manager is not configured")
            await self.permission_manager.sync_role_policies(job.role_id)
            job.status = RoleGrantJobStatus.SYNCED
            job.synced = True
            job.last_error = None
            await self.grant_jobs.update(job)
        except Exception as exc:
            job.status = RoleGrantJobStatus.SYNC_FAILED
            job.synced = False
            job.last_error = str(exc)
            await self.grant_jobs.update(job)
        return RoleGrantResponse(
            role_id=job.role_id, dimension="api", synced=job.synced
        )

    async def retry_failed_grant_jobs(self, limit: int = 20) -> tuple[int, int]:
        jobs = await self.grant_jobs.list_retry_candidates(limit=limit)
        attempted = 0
        succeeded = 0
        for job in jobs:
            if job.id is None:
                continue
            lock_key = f"admin:role_grant:api:{job.role_id}"
            async with redis_lock(key=lock_key, ttl_seconds=30) as got_lock:
                if not got_lock:
                    continue
                attempted += 1
                result = await self.retry_failed_grant_job(job.id)
                if result.synced:
                    succeeded += 1
        return attempted, succeeded

    async def cleanup_synced_grant_jobs(self, limit: int = 100) -> int:
        jobs = await self.grant_jobs.list_cleanup_candidates(limit=limit)
        delete_ids: list[int] = []
        for job in jobs:
            if job.id is None:
                continue
            latest = await self.grant_jobs.find_latest_by_role_id(job.role_id)
            if latest is None:
                continue
            if latest.id == job.id:
                continue
            delete_ids.append(job.id)
        if not delete_ids:
            return 0
        return await self.grant_jobs.delete_jobs(delete_ids)

    async def _apply_api_permissions(
        self,
        *,
        role_id: int,
        api_permission_ids: list[int],
        operator_id: int,
        fingerprint: str,
    ) -> None:
        validated_api_permission_ids = await self._validate_api_permission_ids(
            api_permission_ids
        )
        parent_role_id = await self.roles.get_parent_role_id(role_id)
        if parent_role_id is not None:
            # 接口权限子集校验: 子角色接口权限集合必须是父角色接口权限集合的子集
            parent_api_ids = set(
                await self.roles.get_permission_ids_by_type(
                    parent_role_id, PermissionType.API
                )
            )
            if not set(validated_api_permission_ids).issubset(parent_api_ids):
                raise ValueError("角色接口权限不允许超过上级角色接口权限")

        current_api_ids = set(
            await self.roles.get_permission_ids_by_type(role_id, PermissionType.API)
        )
        removed_ids = current_api_ids - set(validated_api_permission_ids)
        if removed_ids:
            descendant_ids = await self._get_descendant_role_ids(role_id)
            for descendant_id in descendant_ids:
                descendant_api_ids = set(
                    await self.roles.get_permission_ids_by_type(
                        descendant_id, PermissionType.API
                    )
                )
                if descendant_api_ids & removed_ids:
                    raise ValueError("取消权限前先取消下级角色权限")

        try:
            await self.roles.set_permission_ids_by_type(
                role_id=role_id,
                permission_type=PermissionType.API,
                permission_ids=validated_api_permission_ids,
                auto_commit=False,
            )
            await self.roles.session.commit()
        except Exception:
            await self.roles.session.rollback()
            raise
        logger.info(
            "admin.role_api_grant_applied role_id={} fingerprint={} operator_id={} api_permission_count={}",
            role_id,
            fingerprint,
            operator_id,
            len(validated_api_permission_ids),
        )

    async def _validate_api_permission_ids(
        self, permission_ids: list[int]
    ) -> list[int]:
        if not permission_ids:
            return []
        permissions = await self.permissions.get_api_permissions_by_ids(permission_ids)
        found_ids = {int(p.id) for p in permissions if p.id is not None}
        missing_ids = set(permission_ids) - found_ids
        if missing_ids:
            raise ValueError("部分接口权限不存在")
        return sorted(found_ids)

    async def _get_child_role_ids(self, parent_role_id: int) -> list[int]:
        statement = select(Role.id).where(Role.parent_role_id == parent_role_id)
        result = await self.roles.session.exec(statement)
        child_ids: list[int] = []
        for row in result.all():
            cid = row[0] if isinstance(row, (tuple, list)) else row
            if cid is not None:
                child_ids.append(int(cid))
        return child_ids

    async def _get_descendant_role_ids(self, role_id: int) -> list[int]:
        descendants: list[int] = []
        queue: deque[int] = deque([role_id])
        visited: set[int] = {role_id}
        while queue:
            current_id = queue.popleft()
            child_ids = await self._get_child_role_ids(current_id)
            for child_id in child_ids:
                if child_id in visited:
                    continue
                visited.add(child_id)
                descendants.append(child_id)
                queue.append(child_id)
        return descendants

    def _build_scope_rule_entities(
        self, *, role_id: int, data_scope_rules: list[DataScopeRuleUpsert]
    ) -> list[RoleDataScopeRule]:
        result: list[RoleDataScopeRule] = []
        for item in data_scope_rules:
            custom_rule_id = (
                int(item.custom_rule_id) if item.custom_rule_id is not None else None
            )
            view_scope = DataScope(item.view_scope)
            edit_scope = DataScope(item.edit_scope)
            result.append(
                RoleDataScopeRule(
                    role_id=role_id,
                    resource_type=item.resource_type,
                    view_scope=view_scope,
                    edit_scope=edit_scope,
                    custom_rule_id=custom_rule_id,
                    is_active=True,
                )
            )
        return result

    def _normalize_api_permission_ids(self, api_permission_ids: list[int]) -> list[int]:
        return sorted({int(v) for v in api_permission_ids})

    def _normalize_scope_rules(
        self, data_scope_rules: list[DataScopeRuleUpsert]
    ) -> list[DataScopeRuleUpsert]:
        normalized_rules: list[DataScopeRuleUpsert] = []
        for item in data_scope_rules:
            normalized = DataScopeRuleUpsert(
                resource_type=item.resource_type,
                view_scope=str(item.view_scope).split(".")[-1].upper(),
                edit_scope=str(item.edit_scope).split(".")[-1].upper(),
                custom_rule_id=item.custom_rule_id,
            )
            normalized_rules.append(normalized)
        dedup: dict[str, DataScopeRuleUpsert] = {}
        for rule in normalized_rules:
            dedup[rule.resource_type] = rule
        return [dedup[key] for key in sorted(dedup.keys())]

    def _calc_api_fingerprint(
        self,
        *,
        role_id: int,
        api_permission_ids: list[int],
    ) -> str:
        payload = {
            "role_id": role_id,
            "api_permission_ids": api_permission_ids,
        }
        body = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(body).hexdigest()}"

    def _calc_scope_fingerprint(
        self,
        *,
        role_id: int,
        data_scope_rules: list[DataScopeRuleUpsert],
    ) -> str:
        payload = {
            "role_id": role_id,
            "data_scope_rules": [
                {
                    "resource_type": item.resource_type,
                    "view_scope": str(item.view_scope).split(".")[-1].upper(),
                    "edit_scope": str(item.edit_scope).split(".")[-1].upper(),
                    "custom_rule_id": (
                        None
                        if item.custom_rule_id is None
                        else str(item.custom_rule_id)
                    ),
                }
                for item in data_scope_rules
            ],
        }
        body = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return f"sha256:{hashlib.sha256(body).hexdigest()}"


class UserService:
    def __init__(
        self,
        users: UserRepository,
        roles: RoleRepository | None = None,
        permissions: PermissionRepository | None = None,
        permission_manager: IPermissionManager | None = None,
    ) -> None:
        self.users = users
        self.roles = roles
        self.permissions = permissions
        self.permission_manager = permission_manager

    async def list_users(self) -> Sequence[User]:
        return await self.users.list()

    async def list_users_paginated(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[User], int]:
        offset = (page - 1) * page_size
        return await self.users.list_paginated(offset=offset, limit=page_size)

    async def get_roles_by_user_ids(self, user_ids: list[int]) -> dict[int, list[Role]]:
        if not self.roles or not user_ids:
            return {}
        from modules.admin.domain.entities import UserRole

        statement = (
            select(UserRole.user_id, Role)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id.in_(user_ids))
            .order_by(UserRole.user_id, Role.name)
        )
        result = await self.roles.session.exec(statement)
        role_map: dict[int, list[Role]] = {}
        for user_id, role in result.all():
            uid = int(user_id)
            role_map.setdefault(uid, []).append(role)
        return role_map

    async def get_user(self, user_id: int) -> User | None:
        return await self.users.get(user_id)

    async def get_by_username(self, username: str) -> User | None:
        return await self.users.get_by_username(username)

    async def create_user(self, data: UserCreate) -> User:
        password_hash = get_password_hash(data.password)
        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            hashed_password=password_hash,
        )
        return await self.users.create(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> User | None:
        user = await self.users.get(user_id)
        if user is None:
            return None
        old_is_active = user.is_active
        user.username = data.username
        user.email = data.email
        user.full_name = data.full_name
        if data.is_active is not None:
            user.is_active = data.is_active
            if old_is_active != user.is_active:
                user.token_version += 1
        if data.password:
            user.hashed_password = get_password_hash(data.password)
            user.token_version += 1
        user = await self.users.update(user)
        return user

    async def is_protected_user(self, user_id: int) -> bool:
        return await self.users.is_protected_user(user_id)

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self.users.get_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def assign_roles(self, user_id: int, role_ids: list[int]) -> User | None:
        if self.roles is None:
            return None
        user = await self.users.get(user_id)
        if user is None:
            return None
        normalized_role_ids = sorted({int(role_id) for role_id in role_ids})
        if not normalized_role_ids:
            return None
        for role_id in normalized_role_ids:
            role = await self.roles.get(role_id)
            if role is None:
                return None
        await self.users.assign_roles(user_id=user_id, role_ids=normalized_role_ids)
        await self._sync_user_role_grouping_with_fallback(user_id=user_id)
        user = await self.users.get(user_id)
        if user is None:
            return None
        return user

    async def _sync_user_role_grouping_with_fallback(self, *, user_id: int) -> None:
        attempt_delays = (0.0, 0.1, 0.3)
        last_exc: Exception | None = None
        for delay in attempt_delays:
            if delay > 0:
                await asyncio.sleep(delay)
            try:
                if self.permission_manager is None:
                    raise RuntimeError("Permission manager is not configured")
                await self.permission_manager.sync_user_roles(user_id)
                await clear_user_role_sync_retry(user_id=user_id)
                return
            except Exception as incremental_exc:
                last_exc = incremental_exc
                logger.opt(exception=True).warning(
                    "admin.user_role_grouping_incremental_failed user_id={} delay={} error={}",
                    user_id,
                    delay,
                    str(incremental_exc),
                )
        enqueued = await enqueue_user_role_sync_retry(user_id=user_id, delay_seconds=1)
        if enqueued:
            logger.warning(
                "admin.user_role_grouping_deferred user_id={} reason=incremental_failed",
                user_id,
            )
            return
        raise RuntimeError("用户角色同步Casbin失败") from last_exc

    async def get_user_menus(self, user_id: int) -> list[dict]:
        if not self.roles or not self.permissions:
            return []
        role_ids = await self.users.get_role_ids(user_id)
        if not role_ids:
            return []
        menu_ids = set(await self.roles.get_menu_permission_ids_by_role_ids(role_ids))
        if not menu_ids:
            return []
        all_permissions = await self.permissions.list_menu_permissions()
        menu_lookup = {menu.id: menu for menu in all_permissions if menu.id is not None}
        visible_ids = _expand_menu_with_ancestors(menu_ids, menu_lookup)
        return _build_menu_tree_from_ids(visible_ids, menu_lookup, stringify_ids=True)

    async def get_user_roles(self, user_id: int) -> Sequence[Role]:
        if not self.roles:
            return []
        from sqlmodel import select

        from modules.admin.domain.entities import UserRole

        statement = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.roles.session.exec(statement)
        return result.all()
