from fastapi import APIRouter, Depends, HTTPException, status

from app_setup.auth_dependencies import require_permission
from common.responses import ResponseSchema
from modules.admin.api.dependencies import get_admin_permission_service
from modules.admin.api.v1.mappers import (
    to_global_api_permission_list_read,
    to_global_data_scope_list_read,
    to_global_menu_permission_list_read,
)
from modules.admin.api.v1.schemas import (
    GlobalApiPermissionListRead,
    GlobalDataScopeListRead,
    GlobalMenuPermissionListRead,
    MenuPermissionCreate,
    MenuPermissionUpdate,
    RoleMenuItemRead,
)
from modules.admin.application.services import PermissionService

router = APIRouter(prefix="/permissions", tags=["权限"])


@router.get(
    "/menus",
    response_model=ResponseSchema[GlobalMenuPermissionListRead],
    dependencies=[Depends(require_permission())],
    summary="获取全局菜单权限",
)
async def get_global_menu_permissions(
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[GlobalMenuPermissionListRead]:
    dto = await service.get_global_menu_permissions()
    return ResponseSchema(data=to_global_menu_permission_list_read(dto))


@router.get(
    "/api",
    response_model=ResponseSchema[GlobalApiPermissionListRead],
    dependencies=[Depends(require_permission())],
    summary="获取全局接口权限",
)
async def get_global_api_permissions(
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[GlobalApiPermissionListRead]:
    dto = await service.get_global_api_permissions()
    return ResponseSchema(data=to_global_api_permission_list_read(dto))


@router.get(
    "/data",
    response_model=ResponseSchema[GlobalDataScopeListRead],
    dependencies=[Depends(require_permission())],
    summary="获取全局数据权限",
)
async def get_global_data_scope_options(
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[GlobalDataScopeListRead]:
    dto = await service.get_global_data_scope_options()
    return ResponseSchema(data=to_global_data_scope_list_read(dto))


@router.post(
    "/menus",
    response_model=ResponseSchema[RoleMenuItemRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission())],
    summary="添加菜单权限",
)
async def create_menu_permission(
    payload: MenuPermissionCreate,
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[RoleMenuItemRead]:
    try:
        menu = await service.create_menu_permission(
            name=payload.name,
            parent_id=(
                int(payload.parent_id) if payload.parent_id is not None else None
            ),
            path=payload.path,
            component=payload.component,
            icon=payload.icon,
            sort_order=payload.sort_order,
            status=payload.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(
        data=RoleMenuItemRead(
            id=menu.id,
            name=menu.name,
            parent_id=menu.parent_id,
            path=menu.path,
            component=menu.component,
            icon=menu.icon,
            sort_order=menu.sort_order,
            status=menu.status,
            children=[],
        )
    )


@router.put(
    "/menus/{menu_id}",
    response_model=ResponseSchema[RoleMenuItemRead],
    dependencies=[Depends(require_permission())],
    summary="修改菜单权限",
)
async def update_menu_permission(
    menu_id: int,
    payload: MenuPermissionUpdate,
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[RoleMenuItemRead]:
    try:
        menu = await service.update_menu_permission(
            menu_id=menu_id,
            name=payload.name,
            parent_id=(
                int(payload.parent_id) if payload.parent_id is not None else None
            ),
            path=payload.path,
            component=payload.component,
            icon=payload.icon,
            sort_order=payload.sort_order,
            status=payload.status,
        )
    except ValueError as e:
        if str(e) == "菜单不存在":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(
        data=RoleMenuItemRead(
            id=menu.id,
            name=menu.name,
            parent_id=menu.parent_id,
            path=menu.path,
            component=menu.component,
            icon=menu.icon,
            sort_order=menu.sort_order,
            status=menu.status,
            children=[],
        )
    )


@router.delete(
    "/menus/{menu_id}",
    response_model=ResponseSchema[None],
    dependencies=[Depends(require_permission())],
    summary="删除菜单权限",
)
async def delete_menu_permission(
    menu_id: int,
    service: PermissionService = Depends(get_admin_permission_service),
) -> ResponseSchema[None]:
    try:
        await service.delete_menu_permission(menu_id)
    except ValueError as e:
        if str(e) == "菜单不存在":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(data=None)
