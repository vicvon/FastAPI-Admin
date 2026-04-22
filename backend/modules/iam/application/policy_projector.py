from __future__ import annotations

from collections.abc import AsyncIterable

import casbin
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from modules.admin.domain.entities import ApiPermission, Role, RolePermission, UserRole


def build_user_subject(user_id: int) -> str:
    return f"user:{user_id}"


def build_role_subject(role_code: str) -> str:
    return role_code


async def iter_role_policies(
    session: AsyncSession,
) -> AsyncIterable[tuple[str, str, str]]:
    statement = (
        select(Role, ApiPermission)
        .select_from(RolePermission)
        .join(Role, Role.id == RolePermission.role_id)
        .join(ApiPermission, ApiPermission.id == RolePermission.permission_id)
    )
    result = await session.exec(statement)
    for role, permission in result.all():
        if permission.api_path and permission.method:
            yield (
                build_role_subject(role.code),
                permission.api_path,
                permission.method.upper(),
            )


async def iter_grouping_policies(
    session: AsyncSession,
) -> AsyncIterable[tuple[str, str]]:
    statement = (
        select(UserRole, Role)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
    )
    result = await session.exec(statement)
    for user_role, role in result.all():
        yield build_user_subject(user_role.user_id), build_role_subject(role.code)


def _set_auto_notify_watcher(enforcer: casbin.Enforcer, enabled: bool) -> None:
    if hasattr(enforcer, "enable_auto_notify_watcher"):
        enforcer.enable_auto_notify_watcher(enabled)


def _notify_watcher_once(enforcer: casbin.Enforcer) -> None:
    if hasattr(enforcer, "watcher") and enforcer.watcher:
        enforcer.watcher.update()


def _row_first_value(row):
    if isinstance(row, (tuple, list)):
        return row[0] if row else None
    return row


async def sync_policies_from_db(
    session: AsyncSession, enforcer: casbin.Enforcer
) -> None:
    _set_auto_notify_watcher(enforcer, False)
    enforcer.clear_policy()

    async for role_sub, obj, act in iter_role_policies(session):
        enforcer.add_policy(role_sub, obj, act)

    async for user_sub, role_sub in iter_grouping_policies(session):
        enforcer.add_grouping_policy(user_sub, role_sub)

    enforcer.save_policy()
    _set_auto_notify_watcher(enforcer, True)
    _notify_watcher_once(enforcer)


async def sync_role_api_policies_incremental(
    session: AsyncSession, enforcer: casbin.Enforcer, role_id: int
) -> None:
    role = await session.get(Role, role_id)
    if role is None:
        raise ValueError("Role not found")

    role_code = role.code
    statement = (
        select(ApiPermission.api_path, ApiPermission.method)
        .select_from(RolePermission)
        .join(ApiPermission, ApiPermission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == role_id)
    )
    result = await session.exec(statement)

    desired: set[tuple[str, str]] = set()
    for api_path, method in result.all():
        if api_path and method:
            desired.add((api_path, method.upper()))

    current: set[tuple[str, str]] = set()
    for policy in enforcer.get_filtered_policy(0, role_code):
        if len(policy) >= 3:
            current.add((policy[1], str(policy[2]).upper()))

    to_add = desired - current
    to_remove = current - desired

    _set_auto_notify_watcher(enforcer, False)
    try:
        for obj, act in to_remove:
            enforcer.remove_policy(role_code, obj, act)
        for obj, act in to_add:
            enforcer.add_policy(role_code, obj, act)
    finally:
        _set_auto_notify_watcher(enforcer, True)
        _notify_watcher_once(enforcer)


async def sync_user_role_grouping_incremental(
    session: AsyncSession, enforcer: casbin.Enforcer, user_id: int
) -> None:
    user_sub = build_user_subject(user_id)
    statement = (
        select(Role.code)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
    )
    result = await session.exec(statement)
    desired = {_row_first_value(row) for row in result.all()}
    desired = {code for code in desired if code}

    current = set(enforcer.get_roles_for_user(user_sub) or [])
    to_add = desired - current
    to_remove = current - desired

    _set_auto_notify_watcher(enforcer, False)
    try:
        for role_code in to_remove:
            enforcer.remove_grouping_policy(user_sub, role_code)
        for role_code in to_add:
            enforcer.add_grouping_policy(user_sub, role_code)
    finally:
        _set_auto_notify_watcher(enforcer, True)
        _notify_watcher_once(enforcer)
