from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from common.auth import CurrentPrincipal
from common.exceptions import NotFoundError, PermissionError
from common.ports import IDataScopeResolver
from common.responses import ResponseSchema
from core.dependencies import get_db
from modules.admin.api.dependencies import (
    get_current_principal,
    get_data_scope_resolver,
    require_permission,
)
from modules.label_manager.application.services import LabelService
from modules.label_manager.domain.entities import Label
from modules.label_manager.infra.repositories import LabelRepository

from .schemas import (
    LabelCreate,
    LabelEnable,
    LabelMove,
    LabelRead,
    LabelUpdate,
)

router = APIRouter(prefix="/labels", tags=["标签管理"])


async def get_label_service(db: AsyncSession = Depends(get_db)) -> LabelService:
    repo = LabelRepository(db)
    return LabelService(repo)


def _to_label_read(label) -> LabelRead:
    return LabelRead(
        id=str(label.id),
        name=label.name,
        level=label.level,
        parent_id=str(label.parent_id),
        root_id=str(label.root_id),
        path=label.path,
        sort_order=label.sort_order,
        enabled=label.enabled,
        description=label.description,
        created_at=label.created_at,
        updated_at=label.updated_at,
    )


@router.get(
    "/tree",
    response_model=ResponseSchema[list[dict]],
    dependencies=[Depends(require_permission())],
    summary="获取标签树",
)
async def get_label_tree(
    enabled: bool | None = Query(default=None, description="是否启用"),
    service: LabelService = Depends(get_label_service),
):
    data = await service.list_tree(enabled=enabled)
    return ResponseSchema(data=data)


@router.get(
    "",
    response_model=ResponseSchema[list[LabelRead]],
    dependencies=[Depends(require_permission())],
    summary="获取标签列表",
)
async def list_labels(
    parent_id: str | None = Query(default=None, description="父标签ID(一级为0)"),
    level: int | None = Query(default=None, ge=1, le=3, description="层级"),
    keyword: str | None = Query(default=None, description="关键词"),
    enabled: bool | None = Query(default=None, description="是否启用"),
    current_user: CurrentPrincipal = Depends(get_current_principal),
    data_scope_resolver: IDataScopeResolver = Depends(get_data_scope_resolver),
    service: LabelService = Depends(get_label_service),
):
    pid = None if parent_id is None else int(parent_id)
    scope_filter = await data_scope_resolver.build_query_scope(
        user_id=current_user.user_id,
        resource_type="labels",
        action="view",
        model_cls=Label,
    )
    labels = await service.list_labels_with_scope(
        parent_id=pid,
        level=level,
        keyword=keyword,
        enabled=enabled,
        scope_filter=scope_filter,
    )
    return ResponseSchema(data=[_to_label_read(label) for label in labels])


@router.post(
    "",
    response_model=ResponseSchema[LabelRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission())],
    summary="创建标签",
)
async def create_label(
    data: LabelCreate,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: LabelService = Depends(get_label_service),
):
    label = await service.create(
        name=data.name,
        parent_id=int(data.parent_id),
        sort_order=data.sort_order,
        enabled=data.enabled,
        description=data.description,
        operator_id=int(current_user.id),
    )
    return ResponseSchema(data=_to_label_read(label), message="创建成功")


@router.put(
    "/{id}",
    response_model=ResponseSchema[LabelRead],
    dependencies=[Depends(require_permission())],
    summary="更新标签",
)
async def update_label(
    id: str,
    data: LabelUpdate,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    data_scope_resolver: IDataScopeResolver = Depends(get_data_scope_resolver),
    service: LabelService = Depends(get_label_service),
):
    existing = await service.get_by_id(int(id))
    if existing is None:
        raise NotFoundError("数据不存在")
    allowed = await data_scope_resolver.can_operate_entity(
        user_id=current_user.user_id,
        resource_type="labels",
        action="edit",
        entity=existing,
    )
    if not allowed:
        raise PermissionError("无数据操作权限")
    label = await service.update(
        id=int(id),
        name=data.name,
        sort_order=data.sort_order,
        enabled=data.enabled,
        description=data.description,
        operator_id=int(current_user.id),
    )
    return ResponseSchema(data=_to_label_read(label), message="更新成功")


@router.put(
    "/{id}/move",
    response_model=ResponseSchema[LabelRead],
    dependencies=[Depends(require_permission())],
    summary="移动标签",
)
async def move_label(
    id: str,
    data: LabelMove,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: LabelService = Depends(get_label_service),
):
    label = await service.move(
        id=int(id),
        new_parent_id=int(data.new_parent_id),
        operator_id=int(current_user.id),
    )
    return ResponseSchema(data=_to_label_read(label), message="移动成功")


@router.put(
    "/{id}/enable",
    response_model=ResponseSchema[LabelRead],
    dependencies=[Depends(require_permission())],
    summary="启停用标签",
)
async def enable_label(
    id: str,
    data: LabelEnable,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: LabelService = Depends(get_label_service),
):
    label = await service.set_enabled(
        id=int(id), enabled=data.enabled, operator_id=int(current_user.id)
    )
    return ResponseSchema(data=_to_label_read(label), message="更新成功")


@router.delete(
    "/{id}",
    response_model=ResponseSchema[None],
    dependencies=[Depends(require_permission())],
    summary="删除标签",
)
async def delete_label(
    id: str,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    data_scope_resolver: IDataScopeResolver = Depends(get_data_scope_resolver),
    service: LabelService = Depends(get_label_service),
):
    existing = await service.get_by_id(int(id))
    if existing is None:
        raise NotFoundError("数据不存在")
    allowed = await data_scope_resolver.can_operate_entity(
        user_id=current_user.user_id,
        resource_type="labels",
        action="edit",
        entity=existing,
    )
    if not allowed:
        raise PermissionError("无数据操作权限")

    await service.delete(id=int(id), operator_id=int(current_user.id))
    return ResponseSchema(data=None, message="删除成功")
