export interface TokenPayload {
  access_token: string
  refresh_token?: string | null
  token_type: string
  expires_in?: number | null
}

export interface RoleBrief {
  id: string
  name: string
}

export interface RoleItem {
  id: string
  name: string
  code: string
  description?: string | null
  parent_role_id?: string | null
}

export interface UserItem {
  id: string
  username: string
  email: string
  full_name?: string | null
  is_active: boolean
  roles?: RoleBrief[]
}

export interface UserMe extends UserItem {
  roles: RoleItem[]
}

export interface UserListResponse {
  items: UserItem[]
  total: number
  page: number
  page_size: number
}

export interface MenuTreeItem {
  id: string
  name: string
  parent_id?: string | null
  path?: string | null
  component?: string | null
  icon?: string | null
  sort_order: number
  status: string
  children: MenuTreeItem[]
}

export interface ApiPermissionItem {
  id: string
  name: string
  api_path: string
  method: string
  status: string
}

export interface ApiPermissionGroup {
  group_name: string
  permissions: ApiPermissionItem[]
}

export interface DataScopeOption {
  scope: 'SELF' | 'ALL' | 'DEPT' | 'DEPT_AND_SUB' | 'CUSTOM'
  resource_types: string[]
}

export interface RoleDataScopeRule {
  resource_type: string
  custom_rule_id?: string | null
}

export interface RoleDataScopeGroup {
  view_scope: 'SELF' | 'ALL' | 'DEPT' | 'DEPT_AND_SUB' | 'CUSTOM'
  edit_scope: 'SELF' | 'ALL' | 'DEPT' | 'DEPT_AND_SUB' | 'CUSTOM'
  rules: RoleDataScopeRule[]
}

export interface LabelItem {
  id: string
  name: string
  level: number
  parent_id: string
  root_id: string
  path: string
  sort_order: number
  enabled: boolean
  description?: string | null
  created_at: string
  updated_at: string
}

export interface LabelTreeNode extends LabelItem {
  children?: LabelTreeNode[]
}

export interface MenuFormValues {
  name: string
  parent_id?: string | null
  path?: string | null
  component?: string | null
  icon?: string | null
  sort_order?: number
  status: string
}
