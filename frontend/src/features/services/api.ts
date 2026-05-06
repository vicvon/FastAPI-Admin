import { http, unwrapResponse } from '../../lib/http'
import type {
  ApiPermissionGroup,
  DataScopeOption,
  LabelItem,
  LabelTreeNode,
  MenuFormValues,
  MenuTreeItem,
  RoleDataScopeGroup,
  RoleItem,
  TokenPayload,
  UserItem,
  UserListResponse,
  UserMe,
} from '../../types/admin'

export const authApi = {
  async login(username: string, password: string) {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const response = await http.post<TokenPayload>('/api/v1/auth/token', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },
  async logout(refreshToken: string) {
    await http.post('/api/v1/auth/logout', { refresh_token: refreshToken })
  },
}

export const userApi = {
  getCurrentUser() {
    return unwrapResponse<UserMe>(http.get('/api/v1/users/me'))
  },
  list(params: { page: number; page_size: number }) {
    return unwrapResponse<UserListResponse>(http.get('/api/v1/users', { params }))
  },
  create(payload: {
    username: string
    email: string
    full_name?: string
    password: string
  }) {
    return unwrapResponse<UserItem>(http.post('/api/v1/users', payload))
  },
  update(
    userId: string,
    payload: {
      username: string
      email: string
      full_name?: string
      is_active?: boolean
      password?: string
    },
  ) {
    return unwrapResponse<UserItem>(http.put(`/api/v1/users/${userId}`, payload))
  },
  assignRoles(userId: string, roleIds: string[]) {
    return unwrapResponse<UserItem>(
      http.post(`/api/v1/users/${userId}/roles`, { role_ids: roleIds }),
    )
  },
}

export const roleApi = {
  list() {
    return unwrapResponse<RoleItem[]>(http.get('/api/v1/roles'))
  },
  create(payload: { name: string; parent_role_id?: string | null }) {
    return unwrapResponse<RoleItem>(http.post('/api/v1/roles', payload))
  },
  update(roleId: string, payload: { name: string }) {
    return unwrapResponse<RoleItem>(http.put(`/api/v1/roles/${roleId}`, payload))
  },
  getMenus(roleId: string) {
    return unwrapResponse<{ menus: MenuTreeItem[] }>(
      http.get(`/api/v1/roles/${roleId}/menus`),
    )
  },
  saveMenus(roleId: string, menuIds: string[]) {
    return unwrapResponse<{ menu_ids: string[] }>(
      http.put(`/api/v1/roles/${roleId}/menus`, { menu_ids: menuIds }),
    )
  },
  getApiPermissions(roleId: string) {
    return unwrapResponse<{ role_id: string; api_groups: ApiPermissionGroup[] }>(
      http.get(`/api/v1/roles/${roleId}/api-permissions`),
    )
  },
  saveApiPermissions(roleId: string, apiPermissionIds: string[]) {
    return unwrapResponse(
      http.put(`/api/v1/roles/${roleId}/api-permissions`, {
        api_permission_ids: apiPermissionIds,
      }),
    )
  },
  getDataPermissions(roleId: string) {
    return unwrapResponse<{ role_id: string; data_scope_groups: RoleDataScopeGroup[] }>(
      http.get(`/api/v1/roles/${roleId}/data-permissions`),
    )
  },
  saveDataPermissions(
    roleId: string,
    payload: Array<{
      resource_type: string
      view_scope: string
      edit_scope: string
      custom_rule_id?: string | null
    }>,
  ) {
    return unwrapResponse(
      http.put(`/api/v1/roles/${roleId}/data-permissions`, {
        data_scope_rules: payload,
      }),
    )
  },
}

export const permissionApi = {
  getMenus() {
    return unwrapResponse<{ menus: MenuTreeItem[] }>(
      http.get('/api/v1/permissions/menus'),
    )
  },
  createMenu(payload: MenuFormValues) {
    return unwrapResponse(http.post('/api/v1/permissions/menus', payload))
  },
  updateMenu(menuId: string, payload: MenuFormValues) {
    return unwrapResponse(http.put(`/api/v1/permissions/menus/${menuId}`, payload))
  },
  deleteMenu(menuId: string) {
    return unwrapResponse(http.delete(`/api/v1/permissions/menus/${menuId}`))
  },
  getApiPermissions() {
    return unwrapResponse<{ api_groups: ApiPermissionGroup[] }>(
      http.get('/api/v1/permissions/api'),
    )
  },
  getDataScopeOptions() {
    return unwrapResponse<{ data_scope_options: DataScopeOption[] }>(
      http.get('/api/v1/permissions/data'),
    )
  },
}

export const labelApi = {
  list(params?: {
    parent_id?: string
    level?: number
    keyword?: string
    enabled?: boolean
  }) {
    return unwrapResponse<LabelItem[]>(http.get('/api/v1/labels', { params }))
  },
  tree(enabled?: boolean) {
    return unwrapResponse<LabelTreeNode[]>(
      http.get('/api/v1/labels/tree', { params: { enabled } }),
    )
  },
  create(payload: {
    name: string
    parent_id: string
    sort_order: number
    enabled: boolean
    description?: string
  }) {
    return unwrapResponse<LabelItem>(http.post('/api/v1/labels', payload))
  },
  update(
    labelId: string,
    payload: {
      name?: string
      sort_order?: number
      enabled?: boolean
      description?: string
    },
  ) {
    return unwrapResponse<LabelItem>(http.put(`/api/v1/labels/${labelId}`, payload))
  },
  move(labelId: string, newParentId: string) {
    return unwrapResponse<LabelItem>(
      http.put(`/api/v1/labels/${labelId}/move`, {
        new_parent_id: newParentId,
      }),
    )
  },
  remove(labelId: string) {
    return unwrapResponse(http.delete(`/api/v1/labels/${labelId}`))
  },
}
