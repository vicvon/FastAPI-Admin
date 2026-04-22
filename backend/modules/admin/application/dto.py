from __future__ import annotations

from dataclasses import dataclass, field

from modules.admin.domain.entities import DataScope


@dataclass(frozen=True)
class RoleMenuItemDTO:
    id: int
    name: str
    parent_id: int | None
    path: str | None
    component: str | None
    icon: str | None
    sort_order: int
    status: str
    children: list[RoleMenuItemDTO] = field(default_factory=list)


@dataclass(frozen=True)
class RoleApiPermissionDTO:
    id: int
    name: str
    api_path: str
    method: str
    status: str


@dataclass(frozen=True)
class RoleApiGroupDTO:
    group_name: str
    permissions: list[RoleApiPermissionDTO] = field(default_factory=list)


@dataclass(frozen=True)
class RoleDataScopeRuleDTO:
    resource_type: str
    custom_rule_id: int | None = None


@dataclass(frozen=True)
class RoleDataScopeGroupDTO:
    view_scope: DataScope
    edit_scope: DataScope
    rules: list[RoleDataScopeRuleDTO] = field(default_factory=list)


@dataclass(frozen=True)
class RoleApiPermissionListDTO:
    role_id: int
    api_groups: list[RoleApiGroupDTO] = field(default_factory=list)


@dataclass(frozen=True)
class RoleDataScopeListDTO:
    role_id: int
    data_scope_groups: list[RoleDataScopeGroupDTO] = field(default_factory=list)


@dataclass(frozen=True)
class GlobalMenuPermissionListDTO:
    menus: list[RoleMenuItemDTO] = field(default_factory=list)


@dataclass(frozen=True)
class GlobalApiPermissionListDTO:
    api_groups: list[RoleApiGroupDTO] = field(default_factory=list)


@dataclass(frozen=True)
class GlobalDataScopeOptionDTO:
    scope: DataScope
    resource_types: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GlobalDataScopeListDTO:
    data_scope_options: list[GlobalDataScopeOptionDTO] = field(default_factory=list)
