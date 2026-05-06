import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Card,
  Checkbox,
  Col,
  Drawer,
  Empty,
  Form,
  Input,
  Row,
  Select,
  Space,
  Tabs,
  Tree,
  Typography,
} from 'antd'
import type { TreeDataNode } from 'antd'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { PageCard } from '../components/page-card'
import { DATA_SCOPE_OPTIONS } from '../constants/data-scope'
import { permissionApi, roleApi } from '../features/services/api'
import { flattenMenus, toMenuTreeNodes } from '../lib/tree'
import type {
  ApiPermissionGroup,
  DataScopeOption,
  MenuTreeItem,
  RoleDataScopeGroup,
  RoleItem,
} from '../types/admin'

export function RolesPage() {
  const { message } = AntdApp.useApp()
  const [loading, setLoading] = useState(false)
  const [roles, setRoles] = useState<RoleItem[]>([])
  const [menuOptions, setMenuOptions] = useState<MenuTreeItem[]>([])
  const [apiOptions, setApiOptions] = useState<ApiPermissionGroup[]>([])
  const [dataScopeOptions, setDataScopeOptions] = useState<DataScopeOption[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [permissionOpen, setPermissionOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<RoleItem | null>(null)
  const [selectedRole, setSelectedRole] = useState<RoleItem | null>(null)
  const [checkedMenuKeys, setCheckedMenuKeys] = useState<string[]>([])
  const [checkedApiKeys, setCheckedApiKeys] = useState<string[]>([])
  const [scopeRows, setScopeRows] = useState<
    Array<{
      resource_type: string
      view_scope: string
      edit_scope: string
      custom_rule_id?: string
    }>
  >([])
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<{ name: string; parent_role_id?: string | null }>()

  const loadRoles = useCallback(async () => {
    setLoading(true)
    try {
      const [roleData, menus, apis, dataScopes] = await Promise.all([
        roleApi.list(),
        permissionApi.getMenus(),
        permissionApi.getApiPermissions(),
        permissionApi.getDataScopeOptions(),
      ])
      setRoles(roleData)
      setMenuOptions(menus.menus)
      setApiOptions(apis.api_groups)
      setDataScopeOptions(dataScopes.data_scope_options)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色数据加载失败')
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadRoles()
  }, [loadRoles])

  const treeData = useMemo<TreeDataNode[]>(
    () => toMenuTreeNodes(menuOptions),
    [menuOptions],
  )

  const saveRole = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editingRole) {
        await roleApi.update(editingRole.id, { name: values.name })
        message.success('角色更新成功')
      } else {
        await roleApi.create(values)
        message.success('角色创建成功')
      }
      setDrawerOpen(false)
      setEditingRole(null)
      await loadRoles()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色保存失败')
    } finally {
      setSaving(false)
    }
  }

  const openPermissionConfig = async (role: RoleItem) => {
    setSelectedRole(role)
    setPermissionOpen(true)
    setSaving(true)
    try {
      const [menus, apis, scopes] = await Promise.all([
        roleApi.getMenus(role.id),
        roleApi.getApiPermissions(role.id),
        roleApi.getDataPermissions(role.id),
      ])
      setCheckedMenuKeys(flattenMenus(menus.menus).map((item) => item.id))
      setCheckedApiKeys(
        apis.api_groups.flatMap((group) => group.permissions.map((item) => item.id)),
      )
      setScopeRows(mapScopeRows(scopes.data_scope_groups, dataScopeOptions))
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色权限加载失败')
    } finally {
      setSaving(false)
    }
  }

  const savePermissions = async () => {
    if (!selectedRole) return
    setSaving(true)
    try {
      await Promise.all([
        roleApi.saveMenus(selectedRole.id, checkedMenuKeys),
        roleApi.saveApiPermissions(selectedRole.id, checkedApiKeys),
        roleApi.saveDataPermissions(selectedRole.id, scopeRows),
      ])
      message.success('角色权限保存成功')
      setPermissionOpen(false)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色权限保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageCard
      title="角色管理"
      description="管理角色基础信息，并统一配置菜单权限、接口权限和数据权限。"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void loadRoles()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingRole(null)
              form.resetFields()
              setDrawerOpen(true)
            }}
          >
            新建角色
          </Button>
        </Space>
      }
    >
      <Row gutter={[16, 16]}>
        {roles.map((role) => (
          <Col key={role.id} xs={24} lg={12} xl={8}>
            <Card
              loading={loading}
              className="h-full shadow-sm"
              actions={[
                <Button
                  type="link"
                  key="edit"
                  onClick={() => {
                    setEditingRole(role)
                    form.setFieldsValue({
                      name: role.name,
                      parent_role_id: role.parent_role_id || undefined,
                    })
                    setDrawerOpen(true)
                  }}
                >
                  编辑
                </Button>,
                <Button
                  type="link"
                  key="permission"
                  onClick={() => void openPermissionConfig(role)}
                >
                  配置权限
                </Button>,
              ]}
            >
              <Space direction="vertical" size={8}>
                <Typography.Title level={5} className="!mb-0">
                  {role.name}
                </Typography.Title>
                <Typography.Text type="secondary">编码：{role.code}</Typography.Text>
                <Typography.Text type="secondary">
                  父角色：{role.parent_role_id || '--'}
                </Typography.Text>
                <Typography.Paragraph className="!mb-0" ellipsis={{ rows: 2 }}>
                  {role.description || '使用角色配置系统权限与业务授权范围。'}
                </Typography.Paragraph>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
      {!roles.length && !loading ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无角色数据" />
      ) : null}
      <Drawer
        title={editingRole ? '编辑角色' : '新建角色'}
        width={420}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Button type="primary" loading={saving} onClick={() => void saveRole()}>
            保存
          </Button>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>
          {!editingRole ? (
            <Form.Item name="parent_role_id" label="父角色">
              <Select
                allowClear
                placeholder="可选，继承父角色关系"
                options={roles.map((role) => ({
                  label: `${role.name} (${role.code})`,
                  value: role.id,
                }))}
              />
            </Form.Item>
          ) : null}
        </Form>
      </Drawer>
      <Drawer
        title={selectedRole ? `配置角色权限 - ${selectedRole.name}` : '配置角色权限'}
        width={860}
        open={permissionOpen}
        onClose={() => setPermissionOpen(false)}
        extra={
          <Button
            type="primary"
            loading={saving}
            onClick={() => void savePermissions()}
          >
            保存权限
          </Button>
        }
      >
        <Tabs
          items={[
            {
              key: 'menus',
              label: '菜单权限',
              children: (
                <Tree
                  checkable
                  selectable={false}
                  checkedKeys={checkedMenuKeys}
                  onCheck={(keys) => setCheckedMenuKeys(keys as string[])}
                  treeData={treeData}
                  defaultExpandAll
                />
              ),
            },
            {
              key: 'api',
              label: '接口权限',
              children: (
                <Space direction="vertical" size={16} className="w-full">
                  {apiOptions.map((group) => (
                    <Card key={group.group_name} size="small" title={group.group_name}>
                      <Checkbox.Group
                        value={checkedApiKeys}
                        onChange={(value) => setCheckedApiKeys(value as string[])}
                        className="grid gap-3"
                      >
                        {group.permissions.map((permission) => (
                          <Checkbox key={permission.id} value={permission.id}>
                            {permission.name} · {permission.method} {permission.api_path}
                          </Checkbox>
                        ))}
                      </Checkbox.Group>
                    </Card>
                  ))}
                </Space>
              ),
            },
            {
              key: 'data',
              label: '数据权限',
              children: (
                <Space direction="vertical" size={16} className="w-full">
                  {scopeRows.map((row, index) => (
                    <Card
                      key={`${row.resource_type}-${index}`}
                      size="small"
                      title={`资源类型：${row.resource_type}`}
                    >
                      <Row gutter={16}>
                        <Col span={12}>
                          <Typography.Text type="secondary">查看范围</Typography.Text>
                          <Select
                            className="mt-2 w-full"
                            value={row.view_scope}
                            options={DATA_SCOPE_OPTIONS}
                            onChange={(value) => {
                              setScopeRows((current) =>
                                current.map((item, rowIndex) =>
                                  rowIndex === index
                                    ? { ...item, view_scope: value }
                                    : item,
                                ),
                              )
                            }}
                          />
                        </Col>
                        <Col span={12}>
                          <Typography.Text type="secondary">编辑范围</Typography.Text>
                          <Select
                            className="mt-2 w-full"
                            value={row.edit_scope}
                            options={DATA_SCOPE_OPTIONS}
                            onChange={(value) => {
                              setScopeRows((current) =>
                                current.map((item, rowIndex) =>
                                  rowIndex === index
                                    ? { ...item, edit_scope: value }
                                    : item,
                                ),
                              )
                            }}
                          />
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </Space>
              ),
            },
          ]}
        />
      </Drawer>
    </PageCard>
  )
}

function mapScopeRows(groups: RoleDataScopeGroup[], options: DataScopeOption[]) {
  if (!groups.length) {
    return options.map((option) => ({
      resource_type: option.resource_types[0] || '__all__',
      view_scope: option.scope,
      edit_scope: option.scope,
      custom_rule_id: undefined,
    }))
  }

  return groups.map((group) => ({
    resource_type: group.rules[0]?.resource_type || '__all__',
    view_scope: group.view_scope,
    edit_scope: group.edit_scope,
    custom_rule_id: group.rules[0]?.custom_rule_id || undefined,
  }))
}
