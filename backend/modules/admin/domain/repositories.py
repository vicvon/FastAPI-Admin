from __future__ import annotations

import builtins
from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from modules.admin.domain.entities import (
    ApiPermission,
    MenuPermission,
    PermissionType,
    Role,
    RoleDataScopeRule,
    RoleGrantJob,
    User,
    UserDataScopeRule,
)


class BaseRepository(ABC):
    session: AsyncSession


class RoleRepository(BaseRepository):
    @abstractmethod
    async def get(self, role_id: int) -> Role | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def list(self) -> Sequence[Role]: ...

    @abstractmethod
    async def create(self, role: Role) -> Role: ...

    @abstractmethod
    async def update(self, role: Role) -> Role: ...

    @abstractmethod
    async def get_permission_ids(self, role_id: int) -> builtins.list[int]: ...

    @abstractmethod
    async def set_permission_ids(
        self, role_id: int, permission_ids: builtins.list[int], auto_commit: bool = True
    ) -> None: ...

    @abstractmethod
    async def get_permission_ids_by_type(
        self, role_id: int, permission_type: PermissionType
    ) -> builtins.list[int]: ...

    @abstractmethod
    async def get_menu_permission_ids_by_role_ids(
        self, role_ids: builtins.list[int]
    ) -> builtins.list[int]: ...

    @abstractmethod
    async def set_permission_ids_by_type(
        self,
        role_id: int,
        permission_type: PermissionType,
        permission_ids: builtins.list[int],
        auto_commit: bool = True,
    ) -> None: ...

    @abstractmethod
    async def get_parent_role_id(self, role_id: int) -> int | None: ...

    @abstractmethod
    async def set_parent_role_id(
        self, role_id: int, parent_role_id: int | None
    ) -> None: ...


class PermissionRepository(BaseRepository):
    @abstractmethod
    async def list_menu_permissions(self) -> Sequence[MenuPermission]: ...

    @abstractmethod
    async def get_menu_permissions_by_ids(
        self, permission_ids: list[int]
    ) -> Sequence[MenuPermission]: ...

    @abstractmethod
    async def list_api_permissions(self) -> Sequence[ApiPermission]: ...

    @abstractmethod
    async def get_api_permissions_by_ids(
        self, permission_ids: list[int]
    ) -> Sequence[ApiPermission]: ...

    @abstractmethod
    async def get_menu_permission(self, menu_id: int) -> MenuPermission | None: ...

    @abstractmethod
    async def create_menu_permission(self, menu: MenuPermission) -> MenuPermission: ...

    @abstractmethod
    async def update_menu_permission(self, menu: MenuPermission) -> MenuPermission: ...

    @abstractmethod
    async def delete_menu_permission(self, menu_id: int) -> None: ...


class UserRepository(BaseRepository):
    @abstractmethod
    async def get(self, user_id: int) -> User | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list(self) -> Sequence[User]: ...

    @abstractmethod
    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[Sequence[User], int]: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def get_role_ids(self, user_id: int) -> builtins.list[int]: ...

    @abstractmethod
    async def assign_roles(
        self, user_id: int, role_ids: builtins.list[int]
    ) -> None: ...

    @abstractmethod
    async def is_protected_user(self, user_id: int) -> bool: ...


class ScopeRuleRepository(BaseRepository):
    @abstractmethod
    async def replace_role_data_scope_rules(
        self, role_id: int, rules: list[RoleDataScopeRule], auto_commit: bool = True
    ) -> None: ...

    @abstractmethod
    async def find_user_scope_rule(
        self, user_id: int, resource_type: str
    ) -> UserDataScopeRule | None: ...

    @abstractmethod
    async def find_user_scope_rule_with_fallback(
        self, user_id: int, resource_type: str, fallback_resource_type: str = "__all__"
    ) -> UserDataScopeRule | None: ...

    @abstractmethod
    async def find_role_scope_rule(
        self, role_id: int, resource_type: str
    ) -> RoleDataScopeRule | None: ...

    @abstractmethod
    async def find_role_scope_rule_with_fallback(
        self, role_id: int, resource_type: str, fallback_resource_type: str = "__all__"
    ) -> RoleDataScopeRule | None: ...

    @abstractmethod
    async def list_role_scope_rules(
        self, role_id: int
    ) -> Sequence[RoleDataScopeRule]: ...


class RoleGrantJobRepository(BaseRepository):
    @abstractmethod
    async def create(self, job: RoleGrantJob) -> RoleGrantJob: ...

    @abstractmethod
    async def get(self, job_id: int) -> RoleGrantJob | None: ...

    @abstractmethod
    async def find_by_request_id(self, request_id: str) -> RoleGrantJob | None: ...

    @abstractmethod
    async def find_latest_by_role_id(self, role_id: int) -> RoleGrantJob | None: ...

    @abstractmethod
    async def list_retry_candidates(
        self, limit: int = 20
    ) -> Sequence[RoleGrantJob]: ...

    @abstractmethod
    async def list_cleanup_candidates(
        self, limit: int = 100
    ) -> Sequence[RoleGrantJob]: ...

    @abstractmethod
    async def delete_jobs(self, job_ids: list[int]) -> int: ...
