from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    text,
)
from sqlmodel import Field

from core.base import Base
from utils.snowflake import next_snowflake_id


def local_now() -> datetime:
    return datetime.now()


class PermissionType(StrEnum):
    MENU = "MENU"  # 菜单 (显示在侧边栏)
    API = "API"  # 接口 (后端鉴权)


class DataScope(StrEnum):
    SELF = "SELF"
    ALL = "ALL"
    DEPT = "DEPT"
    DEPT_AND_SUB = "DEPT_AND_SUB"
    CUSTOM = "CUSTOM"


class RoleGrantJobStatus(StrEnum):
    APPLYING = "APPLYING"
    SYNCED = "SYNCED"
    SYNC_FAILED = "SYNC_FAILED"


class UserRole(Base, table=True):
    __tablename__ = "user_roles"
    __table_args__ = (
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    user_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    role_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )


class RolePermission(Base, table=True):
    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    role_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    permission_id: int = Field(
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )


class RoleMenuPermission(Base, table=True):
    __tablename__ = "role_menu_permissions"
    __table_args__ = (
        Index("ux_role_menu_permissions", "role_id", "menu_permission_id", unique=True),
        Index("ix_role_menu_permissions_role_id", "role_id"),
        Index("ix_role_menu_permissions_menu_permission_id", "menu_permission_id"),
    )

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    role_id: int = Field(nullable=False, sa_type=BigInteger)
    menu_permission_id: int = Field(nullable=False, sa_type=BigInteger)
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )


class User(Base, table=True):
    __tablename__ = "users"

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(
        default=True,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("1")},
    )
    token_version: int = Field(
        default=0,
        nullable=False,
        sa_type=Integer,
        sa_column_kwargs={"server_default": text("0")},
    )
    full_name: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
    )


class Role(Base, table=True):
    __tablename__ = "roles"

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    name: str = Field(index=True, max_length=50)
    code: str = Field(
        unique=True,
        index=True,
        max_length=100,
        description="Casbin中的角色标识, 如 role:admin",
    )
    description: str | None = Field(default=None, max_length=255)
    is_system: bool = Field(
        default=False,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("0")},
        description="是否系统内置角色",
    )
    parent_role_id: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="父角色ID",
    )
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
    )


class MenuPermission(Base, table=True):
    __tablename__ = "menu_permissions"

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    name: str = Field(max_length=100)
    parent_id: int | None = Field(default=None, sa_type=BigInteger)
    path: str | None = Field(default=None, max_length=255)
    component: str | None = Field(default=None, max_length=255)
    icon: str | None = Field(default=None, max_length=100)
    sort_order: int = Field(
        default=0,
        nullable=False,
        sa_type=Integer,
        sa_column_kwargs={"server_default": text("0")},
    )
    status: str = Field(
        default="ENABLED",
        nullable=False,
        sa_type=String(20),
        sa_column_kwargs={"server_default": text("'ENABLED'")},
    )
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
    )


class ApiPermission(Base, table=True):
    __tablename__ = "api_permissions"

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    name: str = Field(max_length=100)
    group_name: str | None = Field(default=None, max_length=100)
    api_path: str = Field(max_length=255)
    method: str = Field(max_length=20)
    status: str = Field(
        default="ENABLED",
        nullable=False,
        sa_type=String(20),
        sa_column_kwargs={"server_default": text("'ENABLED'")},
    )
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
    )


class RoleDataScopeRule(Base, table=True):
    __tablename__ = "role_data_scope_rules"
    __table_args__ = (
        Index("ux_role_resource", "role_id", "resource_type", unique=True),
        Index("ix_role_resource_active", "role_id", "resource_type", "is_active"),
    )

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    role_id: int = Field(nullable=False, sa_type=BigInteger)
    resource_type: str = Field(max_length=64, nullable=False)
    view_scope: DataScope = Field(
        default=DataScope.SELF,
        nullable=False,
        sa_type=Enum(DataScope, native_enum=False),
        sa_column_kwargs={"server_default": text("'SELF'")},
    )
    edit_scope: DataScope = Field(
        default=DataScope.SELF,
        nullable=False,
        sa_type=Enum(DataScope, native_enum=False),
        sa_column_kwargs={"server_default": text("'SELF'")},
    )
    custom_rule_id: int | None = Field(default=None, sa_type=BigInteger)
    is_active: bool = Field(
        default=True,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("1")},
    )


class UserDataScopeRule(Base, table=True):
    __tablename__ = "user_data_scope_rules"
    __table_args__ = (
        Index("ux_user_resource", "user_id", "resource_type", unique=True),
        Index("ix_user_resource_active", "user_id", "resource_type", "is_active"),
    )

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    user_id: int = Field(nullable=False, sa_type=BigInteger)
    resource_type: str = Field(max_length=64, nullable=False)
    view_scope: DataScope = Field(
        default=DataScope.SELF,
        nullable=False,
        sa_type=Enum(DataScope, native_enum=False),
        sa_column_kwargs={"server_default": text("'SELF'")},
    )
    edit_scope: DataScope = Field(
        default=DataScope.SELF,
        nullable=False,
        sa_type=Enum(DataScope, native_enum=False),
        sa_column_kwargs={"server_default": text("'SELF'")},
    )
    custom_rule_id: int | None = Field(default=None, sa_type=BigInteger)
    is_active: bool = Field(
        default=True,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("1")},
    )


class RoleGrantJob(Base, table=True):
    __tablename__ = "role_grant_jobs"
    __table_args__ = (
        Index("ux_role_grant_request_id", "request_id", unique=True),
        Index("ix_role_grant_role_status", "role_id", "status"),
    )

    id: int = Field(
        default_factory=next_snowflake_id,
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
    )
    role_id: int = Field(nullable=False, sa_type=BigInteger)
    request_id: str = Field(max_length=256, nullable=False)
    api_permission_ids: list[int] = Field(
        default_factory=list,
        nullable=False,
        sa_type=JSON,
    )
    data_scope_rules: list[dict] = Field(
        default_factory=list,
        nullable=False,
        sa_type=JSON,
    )
    operator_id: int = Field(nullable=False, sa_type=BigInteger)
    status: RoleGrantJobStatus = Field(
        default=RoleGrantJobStatus.APPLYING,
        nullable=False,
        sa_type=Enum(RoleGrantJobStatus, native_enum=False),
        sa_column_kwargs={"server_default": text("'APPLYING'")},
    )
    synced: bool = Field(
        default=False,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("0")},
    )
    retry_count: int = Field(
        default=0,
        nullable=False,
        sa_type=Integer,
        sa_column_kwargs={"server_default": text("0")},
    )
    last_error: str | None = Field(default=None, max_length=1024)
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
    )
