from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from common.types import SnowflakeId
from modules.admin.application.contracts import (
    DataScopeRuleUpsert,
    RoleApiGrantRequest,
    RoleCreate,
    RoleDataScopeGrantRequest,
    RoleGrantResponse,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from modules.admin.domain.entities import DataScope, PermissionType

__all__ = [
    "DataScopeRuleUpsert",
    "RoleApiGrantRequest",
    "RoleCreate",
    "RoleDataScopeGrantRequest",
    "RoleGrantResponse",
    "RoleUpdate",
    "UserCreate",
    "UserUpdate",
]


class PermissionBase(BaseModel):
    name: str
    code: str
    type: PermissionType
    description: str | None = None

    # 菜单/资源相关
    parent_id: SnowflakeId | None = None
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    sort_order: int = 0
    api_path: str | None = None
    method: str | None = None


class PermissionCreate(PermissionBase):
    pass


class PermissionRead(PermissionBase):
    id: SnowflakeId


class RoleBase(BaseModel):
    name: str
    code: str
    description: str | None = None


class RoleRead(RoleBase):
    id: SnowflakeId
    permission_ids: list[SnowflakeId] = []
    parent_role_id: SnowflakeId | None = None


class RoleListRead(RoleBase):
    id: SnowflakeId
    parent_role_id: SnowflakeId | None = None


class UserBase(BaseModel):
    username: str
    email: str
    full_name: str | None = None


class UserRead(UserBase):
    id: SnowflakeId
    is_active: bool


class RoleBriefRead(BaseModel):
    id: SnowflakeId
    name: str


class UserListItemRead(UserRead):
    roles: list[RoleBriefRead] = Field(default_factory=list)


class UserListResponse(BaseModel):
    items: list[UserListItemRead] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class UserListQueryParams(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")


class UserMeRead(UserRead):
    roles: list[RoleListRead] = []


class UserDetailRead(UserRead):
    roles: list[RoleListRead] = []


class UserRoleAssign(BaseModel):
    role_ids: list[SnowflakeId] = Field(min_length=1)


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


class CaptchaResponse(BaseModel):
    captcha_id: str
    image: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RoleMenuRead(BaseModel):
    menu_ids: list[SnowflakeId] = []


class RoleMenuUpdate(BaseModel):
    menu_ids: list[SnowflakeId] = []


class RoleMenuItemRead(BaseModel):
    id: SnowflakeId
    name: str
    parent_id: SnowflakeId | None = None
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    sort_order: int = 0
    status: str
    children: list[RoleMenuItemRead] = Field(default_factory=list)


class RoleMenuListRead(BaseModel):
    menus: list[RoleMenuItemRead] = Field(default_factory=list)


class RoleApiPermissionRead(BaseModel):
    id: SnowflakeId
    name: str
    api_path: str
    method: str
    status: str


class RoleApiGroupRead(BaseModel):
    group_name: str
    permissions: list[RoleApiPermissionRead] = Field(default_factory=list)


class RoleDataScopeRuleRead(BaseModel):
    resource_type: str
    custom_rule_id: SnowflakeId | None = None


class RoleDataScopeGroupRead(BaseModel):
    view_scope: DataScope
    edit_scope: DataScope
    rules: list[RoleDataScopeRuleRead] = Field(default_factory=list)


class RolePermissionAndDataScopeRead(BaseModel):
    role_id: SnowflakeId
    api_groups: list[RoleApiGroupRead] = Field(default_factory=list)
    data_scope_groups: list[RoleDataScopeGroupRead] = Field(default_factory=list)


class RoleApiPermissionListRead(BaseModel):
    role_id: SnowflakeId
    api_groups: list[RoleApiGroupRead] = Field(default_factory=list)


class RoleDataScopeListRead(BaseModel):
    role_id: SnowflakeId
    data_scope_groups: list[RoleDataScopeGroupRead] = Field(default_factory=list)


class GlobalDataScopeOptionRead(BaseModel):
    scope: DataScope
    resource_types: list[str] = Field(default_factory=list)


class GlobalMenuPermissionListRead(BaseModel):
    menus: list[RoleMenuItemRead] = Field(default_factory=list)


class GlobalApiPermissionListRead(BaseModel):
    api_groups: list[RoleApiGroupRead] = Field(default_factory=list)


class GlobalDataScopeListRead(BaseModel):
    data_scope_options: list[GlobalDataScopeOptionRead] = Field(default_factory=list)


class MenuPermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    parent_id: SnowflakeId | None = None
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    sort_order: int = 0
    status: str = "ENABLED"


class MenuPermissionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    parent_id: SnowflakeId | None = None
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    sort_order: int = 0
    status: str = "ENABLED"
