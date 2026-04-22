from fastapi import APIRouter, Depends, HTTPException, status

from app_setup.auth_dependencies import get_current_principal, require_permission
from common.auth import CurrentPrincipal
from common.responses import ResponseSchema
from modules.admin.api.dependencies import get_admin_user_service
from modules.admin.api.v1.schemas import (
    RoleListRead,
    UserCreate,
    UserDetailRead,
    UserListItemRead,
    UserListQueryParams,
    UserListResponse,
    UserMeRead,
    UserRead,
    UserRoleAssign,
    UserUpdate,
)
from modules.admin.application.services import UserService

router = APIRouter(prefix="/users", tags=["用户信息"])


@router.get(
    "",
    response_model=ResponseSchema[UserListResponse],
    dependencies=[Depends(require_permission())],
    summary="获取用户列表",
)
async def list_users(
    params: UserListQueryParams = Depends(),
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserListResponse]:
    users, total = await service.list_users_paginated(
        page=params.page, page_size=params.page_size
    )
    user_ids = [int(user.id) for user in users if user.id is not None]
    user_role_map = await service.get_roles_by_user_ids(user_ids)

    items = [
        UserListItemRead(
            id=user.id or 0,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=[
                {"id": role.id or 0, "name": role.name}
                for role in user_role_map.get(int(user.id or 0), [])
            ],
        )
        for user in users
    ]
    return ResponseSchema(
        data=UserListResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )
    )


@router.post(
    "",
    response_model=ResponseSchema[UserRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission())],
    summary="创建用户",
)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserRead]:
    user = await service.create_user(data)
    if user.id is None:
        raise HTTPException(status_code=500, detail="用户ID异常")
    user_read = UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )
    return ResponseSchema(data=user_read)


@router.get(
    "/me",
    response_model=ResponseSchema[UserMeRead],
    summary="获取当前登录用户信息",
)
async def get_me(
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserMeRead]:
    user = await service.get_user(current_user.user_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=401, detail="用户认证失败")

    roles = await service.get_user_roles(current_user.user_id)
    role_data = [
        RoleListRead(
            id=r.id or 0,
            name=r.name,
            code=r.code,
            description=r.description,
            parent_role_id=r.parent_role_id,
        )
        for r in roles
    ]
    data = UserMeRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=role_data,
    )
    return ResponseSchema(data=data)


@router.get(
    "/me/menus",
    response_model=ResponseSchema[list[dict]],
    summary="获取用户页面菜单",
)
async def get_my_menus(
    current_user: CurrentPrincipal = Depends(get_current_principal),
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[list[dict]]:
    menus = await service.get_user_menus(current_user.user_id)
    return ResponseSchema(data=menus)


@router.get(
    "/{user_id}",
    response_model=ResponseSchema[UserDetailRead],
    dependencies=[Depends(require_permission())],
    summary="获取用户详情",
)
async def get_user_detail(
    user_id: int,
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserDetailRead]:
    user = await service.get_user(user_id)
    if user is None or user.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    roles = await service.get_user_roles(user.id)
    role_data = [
        RoleListRead(
            id=r.id or 0,
            name=r.name,
            code=r.code,
            description=r.description,
            parent_role_id=r.parent_role_id,
        )
        for r in roles
    ]
    data = UserDetailRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=role_data,
    )
    return ResponseSchema(data=data)


@router.put(
    "/{user_id}",
    response_model=ResponseSchema[UserRead],
    dependencies=[Depends(require_permission())],
    summary="修改用户信息",
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserRead]:
    if await service.is_protected_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="当前用户不可修改"
        )

    user = await service.update_user(user_id, data)
    if user is None or user.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user_read = UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )
    return ResponseSchema(data=user_read)


@router.post(
    "/{user_id}/roles",
    response_model=ResponseSchema[UserRead],
    dependencies=[Depends(require_permission())],
    summary="用户分配角色(覆盖)",
)
async def assign_role(
    user_id: int,
    data: UserRoleAssign,
    service: UserService = Depends(get_admin_user_service),
) -> ResponseSchema[UserRead]:
    if await service.is_protected_user(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="当前用户不可修改"
        )

    try:
        user = await service.assign_roles(
            user_id=user_id, role_ids=[int(role_id) for role_id in data.role_ids]
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    if user is None or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户或角色不存在"
        )
    user_read = UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )
    return ResponseSchema(data=user_read)
