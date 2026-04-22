from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from common.types import SnowflakeId
from modules.admin.domain.entities import DataScope

ALLOWED_RESOURCE_TYPES = {"__all__", "labels", "audit_records"}


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    parent_role_id: int | None = None


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str


class UserUpdate(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = None


class DataScopeRuleUpsert(BaseModel):
    resource_type: str = "__all__"
    view_scope: DataScope
    edit_scope: DataScope
    custom_rule_id: SnowflakeId | None = None

    @field_validator("resource_type", mode="before")
    @classmethod
    def normalize_resource_type(cls, value: str | None) -> str:
        normalized = "__all__" if value is None else str(value).strip().lower()
        if not normalized:
            normalized = "__all__"
        if normalized not in ALLOWED_RESOURCE_TYPES:
            raise PydanticCustomError(
                "resource_type_invalid",
                "Invalid resource_type",
            )
        return normalized

    @field_validator("view_scope", "edit_scope", mode="before")
    @classmethod
    def normalize_scope(cls, value: str | DataScope) -> str | DataScope:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class RoleGrantResponse(BaseModel):
    role_id: SnowflakeId
    dimension: str
    synced: bool | None = None
    skipped: bool = False


class RoleApiGrantRequest(BaseModel):
    api_permission_ids: list[SnowflakeId] = Field(default_factory=list)


class RoleDataScopeGrantRequest(BaseModel):
    data_scope_rules: list[DataScopeRuleUpsert] = Field(default_factory=list)
