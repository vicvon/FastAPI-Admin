from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import VARCHAR, BigInteger, Boolean, Column, Index, Integer, Text
from sqlmodel import Field

from core.base import Base
from utils.snowflake import next_snowflake_id


class Label(Base, table=True):
    __tablename__ = "labels"
    __table_args__ = (
        Index("ix_labels_ns_parent_sort", "namespace", "parent_id", "sort_order"),
        Index("ix_labels_ns_level", "namespace", "level"),
        Index("ix_labels_ns_root", "namespace", "root_id"),
        Index("ix_labels_ns_enabled", "namespace", "enabled"),
        Index("ix_labels_ns_name", "namespace", "name"),
    )

    id: int = Field(
        default_factory=next_snowflake_id,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=False),
        description="标签ID (Snowflake)",
    )

    namespace: str = Field(
        default="default",
        sa_column=Column(VARCHAR(32), nullable=False),
        description="命名空间(当前版本固定 default)",
    )
    name: str = Field(
        max_length=128,
        sa_column=Column(VARCHAR(128), nullable=False),
        description="标签名称",
    )

    level: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="层级:1/2/3",
    )
    parent_id: int = Field(
        default=0,
        sa_column=Column(BigInteger, nullable=False),
        description="父标签ID(一级为0)",
    )
    root_id: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="一级标签ID",
    )
    path: str = Field(
        max_length=255,
        sa_column=Column(VARCHAR(255), nullable=False),
        description="物化路径,如 /{root_id}/{level2_id}/{id}",
    )

    sort_order: int = Field(
        default=0,
        sa_column=Column(Integer, nullable=False),
        description="同级排序,越小越靠前",
    )
    enabled: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False),
        description="是否启用",
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="描述",
    )

    created_by: int = Field(sa_column=Column(BigInteger), description="创建人ID")
    updated_by: int | None = Field(
        default=None,
        sa_column=Column(BigInteger),
        description="更新人ID",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).astimezone(),
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).astimezone(),
        description="更新时间",
    )
    deleted_at: datetime | None = Field(default=None, description="软删除时间")
