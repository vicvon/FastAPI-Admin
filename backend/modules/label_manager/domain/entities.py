from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    VARCHAR,
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    Text,
    text,
)
from sqlmodel import Field

from core.base import Base
from utils.snowflake import next_snowflake_id


def local_now() -> datetime:
    return datetime.now()


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
        primary_key=True,
        sa_type=BigInteger,
        sa_column_kwargs={"autoincrement": False},
        description="标签ID (Snowflake)",
    )

    namespace: str = Field(
        default="default",
        nullable=False,
        sa_type=VARCHAR(32),
        sa_column_kwargs={"server_default": text("'default'")},
        description="命名空间(当前版本固定 default)",
    )
    name: str = Field(
        max_length=128,
        nullable=False,
        sa_type=VARCHAR(128),
        description="标签名称",
    )

    level: int = Field(
        nullable=False,
        description="层级:1/2/3",
    )
    parent_id: int = Field(
        default=0,
        nullable=False,
        sa_type=BigInteger,
        sa_column_kwargs={"server_default": text("0")},
        description="父标签ID(一级为0)",
    )
    root_id: int = Field(
        nullable=False,
        sa_type=BigInteger,
        description="一级标签ID",
    )
    path: str = Field(
        max_length=255,
        nullable=False,
        sa_type=VARCHAR(255),
        description="物化路径,如 /{root_id}/{level2_id}/{id}",
    )

    sort_order: int = Field(
        default=0,
        nullable=False,
        sa_type=Integer,
        sa_column_kwargs={"server_default": text("0")},
        description="同级排序,越小越靠前",
    )
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_type=Boolean,
        sa_column_kwargs={"server_default": text("1")},
        description="是否启用",
    )
    description: str | None = Field(
        default=None,
        sa_type=Text,
        description="描述",
    )

    created_by: int = Field(sa_type=BigInteger, description="创建人ID")
    updated_by: int | None = Field(
        default=None,
        sa_type=BigInteger,
        description="更新人ID",
    )
    created_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=local_now,
        nullable=False,
        sa_type=DateTime(timezone=False),
        sa_column_kwargs={"onupdate": local_now},
        description="更新时间",
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=False),
        description="软删除时间",
    )
