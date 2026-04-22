from modules.admin.api.v1.schemas import (
    GlobalApiPermissionListRead,
    GlobalDataScopeListRead,
    GlobalDataScopeOptionRead,
    GlobalMenuPermissionListRead,
    RoleApiGroupRead,
    RoleApiPermissionListRead,
    RoleApiPermissionRead,
    RoleDataScopeGroupRead,
    RoleDataScopeListRead,
    RoleDataScopeRuleRead,
    RoleMenuItemRead,
)
from modules.admin.application.dto import (
    GlobalApiPermissionListDTO,
    GlobalDataScopeListDTO,
    GlobalMenuPermissionListDTO,
    RoleApiPermissionListDTO,
    RoleDataScopeListDTO,
    RoleMenuItemDTO,
)


def to_role_menu_item_read(dto: RoleMenuItemDTO) -> RoleMenuItemRead:
    return RoleMenuItemRead(
        id=dto.id,
        name=dto.name,
        parent_id=dto.parent_id,
        path=dto.path,
        component=dto.component,
        icon=dto.icon,
        sort_order=dto.sort_order,
        status=dto.status,
        children=[to_role_menu_item_read(child) for child in dto.children],
    )


def to_role_api_permission_list_read(
    dto: RoleApiPermissionListDTO,
) -> RoleApiPermissionListRead:
    return RoleApiPermissionListRead(
        role_id=dto.role_id,
        api_groups=[
            RoleApiGroupRead(
                group_name=group.group_name,
                permissions=[
                    RoleApiPermissionRead(
                        id=permission.id,
                        name=permission.name,
                        api_path=permission.api_path,
                        method=permission.method,
                        status=permission.status,
                    )
                    for permission in group.permissions
                ],
            )
            for group in dto.api_groups
        ],
    )


def to_role_data_scope_list_read(dto: RoleDataScopeListDTO) -> RoleDataScopeListRead:
    return RoleDataScopeListRead(
        role_id=dto.role_id,
        data_scope_groups=[
            RoleDataScopeGroupRead(
                view_scope=group.view_scope,
                edit_scope=group.edit_scope,
                rules=[
                    RoleDataScopeRuleRead(
                        resource_type=rule.resource_type,
                        custom_rule_id=rule.custom_rule_id,
                    )
                    for rule in group.rules
                ],
            )
            for group in dto.data_scope_groups
        ],
    )


def to_global_menu_permission_list_read(
    dto: GlobalMenuPermissionListDTO,
) -> GlobalMenuPermissionListRead:
    return GlobalMenuPermissionListRead(
        menus=[to_role_menu_item_read(item) for item in dto.menus]
    )


def to_global_api_permission_list_read(
    dto: GlobalApiPermissionListDTO,
) -> GlobalApiPermissionListRead:
    return GlobalApiPermissionListRead(
        api_groups=[
            RoleApiGroupRead(
                group_name=group.group_name,
                permissions=[
                    RoleApiPermissionRead(
                        id=permission.id,
                        name=permission.name,
                        api_path=permission.api_path,
                        method=permission.method,
                        status=permission.status,
                    )
                    for permission in group.permissions
                ],
            )
            for group in dto.api_groups
        ]
    )


def to_global_data_scope_list_read(
    dto: GlobalDataScopeListDTO,
) -> GlobalDataScopeListRead:
    return GlobalDataScopeListRead(
        data_scope_options=[
            GlobalDataScopeOptionRead(
                scope=option.scope,
                resource_types=option.resource_types,
            )
            for option in dto.data_scope_options
        ]
    )
