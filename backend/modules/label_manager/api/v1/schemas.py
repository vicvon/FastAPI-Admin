from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from common.types import SnowflakeId


class LabelCreate(BaseModel):
    name: str = Field(..., max_length=128, description="标签名称")
    parent_id: SnowflakeId = Field(default="0", description="父标签ID(一级为0)")
    sort_order: int = Field(default=0, description="同级排序")
    enabled: bool = Field(default=True, description="是否启用")
    description: str | None = Field(default=None, description="描述")


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=128, description="标签名称")
    sort_order: int | None = Field(default=None, description="同级排序")
    enabled: bool | None = Field(default=None, description="是否启用")
    description: str | None = Field(default=None, description="描述")


class LabelMove(BaseModel):
    new_parent_id: SnowflakeId = Field(..., description="新父标签ID(一级为0)")


class LabelEnable(BaseModel):
    enabled: bool = Field(..., description="是否启用")


class LabelRead(BaseModel):
    id: SnowflakeId = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    level: int = Field(..., description="层级")
    parent_id: SnowflakeId = Field(..., description="父标签ID")
    root_id: SnowflakeId = Field(..., description="一级标签ID")
    path: str = Field(..., description="物化路径")
    sort_order: int = Field(..., description="同级排序")
    enabled: bool = Field(..., description="是否启用")
    description: str | None = Field(default=None, description="描述")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class LabelTreeNode(LabelRead):
    children: list[LabelTreeNode] = Field(default_factory=list, description="子节点")


LabelTreeNode.model_rebuild()


class LabelListResponse(BaseModel):
    items: list[LabelListItem] = Field(..., description="标签列表")
    page_actions: PageActions = Field(..., description="页面动作权限")


class LabelTreeResponse(BaseModel):
    items: list[LabelTreeNode] = Field(..., description="标签树")


class RowActions(BaseModel):
    can_edit: bool
    can_delete: bool
    deny_reason: str | None = None


class PageActions(BaseModel):
    can_batch_export: bool
    can_batch_delete: bool


class LabelListItem(LabelRead):
    row_actions: RowActions


LabelListItem.model_rebuild()
