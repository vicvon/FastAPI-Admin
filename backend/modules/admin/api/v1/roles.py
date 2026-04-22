from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status

from common.auth import CurrentPrincipal
from common.responses import ResponseSchema
from modules.admin.api.dependencies import (
    get_admin_role_permission_app_service,
    get_admin_role_service,
    get_current_principal,
    require_permission,
)
from modules.admin.api.v1.mappers import (
    to_role_api_permission_list_read,
    to_role_data_scope_list_read,
)
from modules.admin.api.v1.schemas import (
    RoleApiGrantRequest,
    RoleApiPermissionListRead,
    RoleCreate,
    RoleDataScopeGrantRequest,
    RoleDataScopeListRead,
    RoleGrantResponse,
    RoleListRead,
    RoleMenuListRead,
    RoleMenuRead,
    RoleMenuUpdate,
    RoleRead,
    RoleUpdate,
)
from modules.admin.application.services import (
    RolePermissionApplicationService,
    RoleService,
)

router = APIRouter(prefix="/roles", tags=["角色"])


@router.get(
    "",
    response_model=ResponseSchema[list[RoleListRead]],
    dependencies=[Depends(require_permission())],
    summary="获取角色列表",
)
async def list_roles(
    service: RoleService = Depends(get_admin_role_service),
) -> ResponseSchema[Sequence[RoleListRead]]:
    roles = await service.list_roles()
    data = []
    for role in roles:
        parent_role_id = None
        # 隐藏系统内置角色(包含历史兼容规则)
        if await service.is_protected_role(role):
            continue

        if role.id is not None:
            parent_role_id = await service.get_parent_role_id(role.id)

        data.append(
            RoleListRead(
                id=role.id or 0,
                name=role.name,
                code=role.code,
                description=role.description,
                parent_role_id=parent_role_id,
            )
        )
    return ResponseSchema(data=data)


@router.post(
    "",
    response_model=ResponseSchema[RoleRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission())],
    summary="创建角色",
)
async def create_role(
    data: RoleCreate,
    service: RoleService = Depends(get_admin_role_service),
) -> ResponseSchema[RoleRead]:
    try:
        role = await service.create_role(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    if role.id is None:
        raise HTTPException(status_code=500, detail="角色ID异常")

    permission_ids = await service.get_permission_ids(role.id)
    parent_role_id = await service.get_parent_role_id(role.id)

    role_read = RoleRead(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        permission_ids=permission_ids,
        parent_role_id=parent_role_id,
    )
    return ResponseSchema(data=role_read)


@router.put(
    "/{role_id}",
    response_model=ResponseSchema[RoleRead],
    dependencies=[Depends(require_permission())],
    summary="修改角色信息",
)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    service: RoleService = Depends(get_admin_role_service),
) -> ResponseSchema[RoleRead]:
    try:
        role = await service.update_role(role_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    if role is None or role.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    permission_ids = await service.get_permission_ids(role.id)
    parent_role_id = await service.get_parent_role_id(role.id)

    role_read = RoleRead(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        permission_ids=permission_ids,
        parent_role_id=parent_role_id,
    )
    return ResponseSchema(data=role_read)


@router.put(
    "/{role_id}/api-permissions",
    response_model=ResponseSchema[RoleGrantResponse],
    dependencies=[Depends(require_permission())],
    summary="保存角色接口权限",
)
async def grant_role_api_permissions(
    role_id: int,
    payload: RoleApiGrantRequest,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: RolePermissionApplicationService = Depends(
        get_admin_role_permission_app_service
    ),
) -> ResponseSchema[RoleGrantResponse]:
    try:
        result = await service.grant_api_permissions(
            role_id=role_id,
            api_permission_ids=[int(v) for v in payload.api_permission_ids],
            operator_id=current_user.user_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(data=result)


@router.put(
    "/{role_id}/data-permissions",
    response_model=ResponseSchema[RoleGrantResponse],
    dependencies=[Depends(require_permission())],
    summary="保存角色数据权限",
)
async def grant_role_data_permissions(
    role_id: int,
    payload: RoleDataScopeGrantRequest,
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: RolePermissionApplicationService = Depends(
        get_admin_role_permission_app_service
    ),
) -> ResponseSchema[RoleGrantResponse]:
    try:
        result = await service.grant_data_scopes(
            role_id=role_id,
            data_scope_rules=payload.data_scope_rules,
            operator_id=current_user.user_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(data=result)


@router.get(
    "/{role_id}/api-permissions",
    response_model=ResponseSchema[RoleApiPermissionListRead],
    dependencies=[Depends(require_permission())],
    summary="获取角色接口权限列表",
)
async def get_role_api_permissions(
    role_id: int,
    service: RolePermissionApplicationService = Depends(
        get_admin_role_permission_app_service
    ),
) -> ResponseSchema[RoleApiPermissionListRead]:
    try:
        dto = await service.get_role_api_permissions(role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return ResponseSchema(data=to_role_api_permission_list_read(dto))


@router.get(
    "/{role_id}/data-permissions",
    response_model=ResponseSchema[RoleDataScopeListRead],
    dependencies=[Depends(require_permission())],
    summary="获取角色数据权限列表",
)
async def get_role_data_permissions(
    role_id: int,
    service: RolePermissionApplicationService = Depends(
        get_admin_role_permission_app_service
    ),
) -> ResponseSchema[RoleDataScopeListRead]:
    try:
        dto = await service.get_role_data_scopes(role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return ResponseSchema(data=to_role_data_scope_list_read(dto))


@router.get(
    "/{role_id}/menus",
    response_model=ResponseSchema[RoleMenuListRead],
    dependencies=[Depends(require_permission())],
    summary="获取角色菜单权限",
)
async def get_role_menus(
    role_id: int,
    service: RoleService = Depends(get_admin_role_service),
) -> ResponseSchema[RoleMenuListRead]:
    try:
        menu_tree = await service.get_role_menu_detail_tree(role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return ResponseSchema(data=RoleMenuListRead(menus=menu_tree))


@router.put(
    "/{role_id}/menus",
    response_model=ResponseSchema[RoleMenuRead],
    dependencies=[Depends(require_permission())],
    summary="保存角色菜单权限",
)
async def update_role_menus(
    role_id: int,
    payload: RoleMenuUpdate,
    service: RoleService = Depends(get_admin_role_service),
) -> ResponseSchema[RoleMenuRead]:
    try:
        menu_ids = [int(v) for v in payload.menu_ids]
        await service.set_role_menu_ids(role_id, menu_ids, include_ancestors=True)
        saved_ids = await service.get_role_menu_ids(role_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return ResponseSchema(data=RoleMenuRead(menu_ids=saved_ids))
