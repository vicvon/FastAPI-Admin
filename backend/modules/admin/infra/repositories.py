from __future__ import annotations

import builtins
from collections.abc import Sequence

from sqlalchemy import case, delete, func, or_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from modules.admin.domain.entities import (
    ApiPermission,
    MenuPermission,
    PermissionType,
    Role,
    RoleDataScopeRule,
    RoleGrantJob,
    RoleGrantJobStatus,
    RoleMenuPermission,
    RolePermission,
    User,
    UserDataScopeRule,
    UserRole,
)
from modules.admin.domain.repositories import (
    BaseRepository as BaseRepositoryInterface,
    PermissionRepository as PermissionRepositoryInterface,
    RoleGrantJobRepository as RoleGrantJobRepositoryInterface,
    RoleRepository as RoleRepositoryInterface,
    ScopeRuleRepository as ScopeRuleRepositoryInterface,
    UserRepository as UserRepositoryInterface,
)
from modules.admin.domain.system_semantics import (
    LEGACY_SYSTEM_ROLE_ID,
    LEGACY_SYSTEM_USER_ID,
    SYSTEM_ROLE_CODES,
)


class BaseRepository(BaseRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class RoleRepository(BaseRepository, RoleRepositoryInterface):
    async def get(self, role_id: int) -> Role | None:
        return await self.session.get(Role, role_id)

    async def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)
        result = await self.session.exec(statement)
        return result.first()

    async def list(self) -> Sequence[Role]:
        statement = select(Role)
        result = await self.session.exec(statement)
        return result.all()

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def update(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def get_permission_ids(self, role_id: int) -> builtins.list[int]:
        statement = select(RolePermission.permission_id).where(
            RolePermission.role_id == role_id
        )
        result = await self.session.exec(statement)
        return list(result.all())

    async def set_permission_ids(
        self, role_id: int, permission_ids: builtins.list[int], auto_commit: bool = True
    ) -> None:
        await self.session.exec(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for permission_id in permission_ids:
            self.session.add(
                RolePermission(role_id=role_id, permission_id=permission_id)
            )
        if auto_commit:
            await self.session.commit()

    async def get_permission_ids_by_type(
        self, role_id: int, permission_type: PermissionType
    ) -> builtins.list[int]:
        if permission_type == PermissionType.MENU:
            statement = select(RoleMenuPermission.menu_permission_id).where(
                RoleMenuPermission.role_id == role_id
            )
            result = await self.session.exec(statement)
            return list(result.all())
        if permission_type == PermissionType.API:
            statement = (
                select(RolePermission.permission_id)
                .join(ApiPermission, ApiPermission.id == RolePermission.permission_id)
                .where(RolePermission.role_id == role_id)
            )
            result = await self.session.exec(statement)
            return list(result.all())
        raise ValueError("Unsupported permission type")

    async def get_menu_permission_ids_by_role_ids(
        self, role_ids: builtins.list[int]
    ) -> builtins.list[int]:
        if not role_ids:
            return []
        statement = select(RoleMenuPermission.menu_permission_id).where(
            RoleMenuPermission.role_id.in_(role_ids)
        )
        result = await self.session.exec(statement)
        return list({int(v) for v in result.all() if v is not None})

    async def set_permission_ids_by_type(
        self,
        role_id: int,
        permission_type: PermissionType,
        permission_ids: builtins.list[int],
        auto_commit: bool = True,
    ) -> None:
        if permission_type == PermissionType.MENU:
            await self.session.exec(
                delete(RoleMenuPermission).where(RoleMenuPermission.role_id == role_id)
            )
            for permission_id in permission_ids:
                self.session.add(
                    RoleMenuPermission(
                        role_id=role_id, menu_permission_id=permission_id
                    )
                )
            if auto_commit:
                await self.session.commit()
            return
        if permission_type == PermissionType.API:
            await self.session.exec(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )
            for permission_id in permission_ids:
                self.session.add(
                    RolePermission(role_id=role_id, permission_id=permission_id)
                )
            if auto_commit:
                await self.session.commit()
            return
        raise ValueError("Unsupported permission type")

    async def get_parent_role_id(self, role_id: int) -> int | None:
        role = await self.get(role_id)
        if role is None:
            return None
        return role.parent_role_id

    async def set_parent_role_id(
        self, role_id: int, parent_role_id: int | None
    ) -> None:
        role = await self.get(role_id)
        if role is None:
            return
        role.parent_role_id = parent_role_id
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)


class PermissionRepository(BaseRepository, PermissionRepositoryInterface):
    async def list_menu_permissions(self) -> Sequence[MenuPermission]:
        statement = select(MenuPermission)
        result = await self.session.exec(statement)
        return result.all()

    async def get_menu_permissions_by_ids(
        self, permission_ids: list[int]
    ) -> Sequence[MenuPermission]:
        if not permission_ids:
            return []
        statement = select(MenuPermission).where(MenuPermission.id.in_(permission_ids))
        result = await self.session.exec(statement)
        return result.all()

    async def list_api_permissions(self) -> Sequence[ApiPermission]:
        statement = select(ApiPermission)
        result = await self.session.exec(statement)
        return result.all()

    async def get_api_permissions_by_ids(
        self, permission_ids: list[int]
    ) -> Sequence[ApiPermission]:
        if not permission_ids:
            return []
        statement = select(ApiPermission).where(ApiPermission.id.in_(permission_ids))
        result = await self.session.exec(statement)
        return result.all()

    async def get_menu_permission(self, menu_id: int) -> MenuPermission | None:
        return await self.session.get(MenuPermission, menu_id)

    async def create_menu_permission(self, menu: MenuPermission) -> MenuPermission:
        self.session.add(menu)
        await self.session.commit()
        await self.session.refresh(menu)
        return menu

    async def update_menu_permission(self, menu: MenuPermission) -> MenuPermission:
        self.session.add(menu)
        await self.session.commit()
        await self.session.refresh(menu)
        return menu

    async def delete_menu_permission(self, menu_id: int) -> None:
        await self.session.exec(
            delete(RoleMenuPermission).where(
                RoleMenuPermission.menu_permission_id == menu_id
            )
        )
        await self.session.exec(
            delete(MenuPermission).where(MenuPermission.id == menu_id)
        )
        await self.session.commit()


class UserRepository(BaseRepository, UserRepositoryInterface):
    def _protected_role_expr(self):
        return or_(
            Role.is_system.is_(True),
            Role.id == LEGACY_SYSTEM_ROLE_ID,
            Role.code.in_(tuple(SYSTEM_ROLE_CODES)),
        )

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.exec(statement)
        return result.first()

    async def list(self) -> Sequence[User]:
        statement = select(User)
        result = await self.session.exec(statement)
        return result.all()

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[Sequence[User], int]:
        protected_user_ids = (
            select(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(self._protected_role_expr())
        )
        base_statement = (
            select(User)
            .where(User.id != LEGACY_SYSTEM_USER_ID)
            .where(User.id.not_in(protected_user_ids))
        )
        statement = base_statement.order_by(User.id).offset(offset).limit(limit)
        result = await self.session.exec(statement)
        users = result.all()

        count_statement = (
            select(func.count())
            .select_from(User)
            .where(User.id != LEGACY_SYSTEM_USER_ID)
            .where(User.id.not_in(protected_user_ids))
        )
        count_result = await self.session.exec(count_statement)
        total = int(count_result.one() or 0)
        return users, total

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_role_ids(self, user_id: int) -> builtins.list[int]:
        statement = select(UserRole.role_id).where(UserRole.user_id == user_id)
        result = await self.session.exec(statement)
        return list(result.all())

    async def assign_roles(self, user_id: int, role_ids: builtins.list[int]) -> None:
        normalized_role_ids = sorted({int(role_id) for role_id in role_ids})
        await self.session.exec(delete(UserRole).where(UserRole.user_id == user_id))
        for role_id in normalized_role_ids:
            self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.commit()

    async def is_protected_user(self, user_id: int) -> bool:
        if user_id == LEGACY_SYSTEM_USER_ID:
            return True
        statement = (
            select(func.count())
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
            .where(self._protected_role_expr())
        )
        result = await self.session.exec(statement)
        return int(result.one() or 0) > 0


class ScopeRuleRepository(BaseRepository, ScopeRuleRepositoryInterface):
    async def replace_role_data_scope_rules(
        self, role_id: int, rules: list[RoleDataScopeRule], auto_commit: bool = True
    ) -> None:
        await self.session.exec(
            delete(RoleDataScopeRule).where(RoleDataScopeRule.role_id == role_id)
        )
        for rule in rules:
            self.session.add(
                RoleDataScopeRule(
                    role_id=role_id,
                    resource_type=rule.resource_type,
                    view_scope=rule.view_scope,
                    edit_scope=rule.edit_scope,
                    custom_rule_id=rule.custom_rule_id,
                    is_active=rule.is_active,
                )
            )
        if auto_commit:
            await self.session.commit()

    async def find_user_scope_rule(
        self, user_id: int, resource_type: str
    ) -> UserDataScopeRule | None:
        statement = (
            select(UserDataScopeRule)
            .where(UserDataScopeRule.user_id == user_id)
            .where(UserDataScopeRule.resource_type == resource_type)
            .where(UserDataScopeRule.is_active.is_(True))
        )
        result = await self.session.exec(statement)
        return result.first()

    async def find_user_scope_rule_with_fallback(
        self, user_id: int, resource_type: str, fallback_resource_type: str = "__all__"
    ) -> UserDataScopeRule | None:
        resource_types = [resource_type]
        if resource_type != fallback_resource_type:
            resource_types.append(fallback_resource_type)
        statement = (
            select(UserDataScopeRule)
            .where(UserDataScopeRule.user_id == user_id)
            .where(UserDataScopeRule.resource_type.in_(resource_types))
            .where(UserDataScopeRule.is_active.is_(True))
            .order_by(
                case((UserDataScopeRule.resource_type == resource_type, 0), else_=1)
            )
        )
        result = await self.session.exec(statement)
        return result.first()

    async def find_role_scope_rule(
        self, role_id: int, resource_type: str
    ) -> RoleDataScopeRule | None:
        statement = (
            select(RoleDataScopeRule)
            .where(RoleDataScopeRule.role_id == role_id)
            .where(RoleDataScopeRule.resource_type == resource_type)
            .where(RoleDataScopeRule.is_active.is_(True))
        )
        result = await self.session.exec(statement)
        return result.first()

    async def find_role_scope_rule_with_fallback(
        self, role_id: int, resource_type: str, fallback_resource_type: str = "__all__"
    ) -> RoleDataScopeRule | None:
        resource_types = [resource_type]
        if resource_type != fallback_resource_type:
            resource_types.append(fallback_resource_type)
        statement = (
            select(RoleDataScopeRule)
            .where(RoleDataScopeRule.role_id == role_id)
            .where(RoleDataScopeRule.resource_type.in_(resource_types))
            .where(RoleDataScopeRule.is_active.is_(True))
            .order_by(
                case((RoleDataScopeRule.resource_type == resource_type, 0), else_=1)
            )
        )
        result = await self.session.exec(statement)
        return result.first()

    async def list_role_scope_rules(self, role_id: int) -> Sequence[RoleDataScopeRule]:
        statement = (
            select(RoleDataScopeRule)
            .where(RoleDataScopeRule.role_id == role_id)
            .where(RoleDataScopeRule.is_active.is_(True))
            .order_by(RoleDataScopeRule.resource_type.asc())
        )
        result = await self.session.exec(statement)
        return result.all()


class RoleGrantJobRepository(BaseRepository, RoleGrantJobRepositoryInterface):
    async def create(self, job: RoleGrantJob) -> RoleGrantJob:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: int) -> RoleGrantJob | None:
        return await self.session.get(RoleGrantJob, job_id)

    async def find_by_request_id(self, request_id: str) -> RoleGrantJob | None:
        statement = select(RoleGrantJob).where(RoleGrantJob.request_id == request_id)
        result = await self.session.exec(statement)
        return result.first()

    async def find_latest_by_role_id(self, role_id: int) -> RoleGrantJob | None:
        statement = (
            select(RoleGrantJob)
            .where(RoleGrantJob.role_id == role_id)
            .order_by(RoleGrantJob.created_at.desc(), RoleGrantJob.id.desc())
        )
        result = await self.session.exec(statement)
        return result.first()

    async def list_retry_candidates(self, limit: int = 20) -> Sequence[RoleGrantJob]:
        statement = (
            select(RoleGrantJob)
            .where(RoleGrantJob.status == RoleGrantJobStatus.SYNC_FAILED)
            .order_by(RoleGrantJob.updated_at.asc(), RoleGrantJob.id.asc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def update(self, job: RoleGrantJob) -> RoleGrantJob:
        if job.status == RoleGrantJobStatus.SYNC_FAILED:
            job.retry_count += 1
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def list_cleanup_candidates(self, limit: int = 100) -> Sequence[RoleGrantJob]:
        statement = (
            select(RoleGrantJob)
            .where(RoleGrantJob.status == RoleGrantJobStatus.SYNCED)
            .order_by(RoleGrantJob.updated_at.asc(), RoleGrantJob.id.asc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def delete_jobs(self, job_ids: list[int]) -> int:
        if not job_ids:
            return 0
        await self.session.exec(
            delete(RoleGrantJob).where(RoleGrantJob.id.in_(job_ids))
        )
        await self.session.commit()
        return len(job_ids)
