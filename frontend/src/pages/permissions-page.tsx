import { DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Card,
  Drawer,
  Empty,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'

import { PageCard } from '../components/page-card'
import { permissionApi } from '../features/services/api'
import { flattenMenus } from '../lib/tree'
import type { ApiPermissionGroup, DataScopeOption, MenuFormValues, MenuTreeItem } from '../types/admin'

export function PermissionsPage({
  defaultTab = 'menus',
}: {
  defaultTab?: 'menus' | 'apis' | 'data'
}) {
  const { message } = AntdApp.useApp()
  const [loading, setLoading] = useState(false)
  const [menus, setMenus] = useState<MenuTreeItem[]>([])
  const [apiGroups, setApiGroups] = useState<ApiPermissionGroup[]>([])
  const [dataScopes, setDataScopes] = useState<DataScopeOption[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingMenu, setEditingMenu] = useState<MenuTreeItem | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<MenuFormValues>()

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [menuData, apiData, dataScopeData] = await Promise.all([
        permissionApi.getMenus(),
        permissionApi.getApiPermissions(),
        permissionApi.getDataScopeOptions(),
      ])
      setMenus(menuData.menus)
      setApiGroups(apiData.api_groups)
      setDataScopes(dataScopeData.data_scope_options)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '权限数据加载失败')
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const columns: ColumnsType<MenuTreeItem> = [
    { title: '菜单名称', dataIndex: 'name', key: 'name', width: 180 },
    {
      title: '路由路径',
      dataIndex: 'path',
      key: 'path',
      render: (value) => value || '--',
    },
    {
      title: '组件',
      dataIndex: 'component',
      key: 'component',
      render: (value) => value || '--',
    },
    { title: '图标', dataIndex: 'icon', key: 'icon', render: (value) => value || '--' },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 90 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (value) => (
        <Tag color={value === 'ENABLED' ? 'success' : 'default'}>{value}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 140,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            onClick={() => {
              setEditingMenu(record)
              form.setFieldsValue(record)
              setDrawerOpen(true)
            }}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除该菜单吗？"
            onConfirm={() => void deleteMenu(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const deleteMenu = async (menuId: string) => {
    try {
      await permissionApi.deleteMenu(menuId)
      message.success('菜单删除成功')
      await loadAll()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '菜单删除失败')
    }
  }

  const saveMenu = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editingMenu) {
        await permissionApi.updateMenu(editingMenu.id, values)
        message.success('菜单更新成功')
      } else {
        await permissionApi.createMenu(values)
        message.success('菜单创建成功')
      }
      setDrawerOpen(false)
      await loadAll()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '菜单保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageCard
      title="权限中心"
      description="集中查看菜单权限、接口权限和数据权限选项，支持维护菜单节点。"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void loadAll()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingMenu(null)
              form.resetFields()
              form.setFieldsValue({ status: 'ENABLED', sort_order: 0 })
              setDrawerOpen(true)
            }}
          >
            新建菜单
          </Button>
        </Space>
      }
    >
      <Tabs
        defaultActiveKey={defaultTab}
        items={[
          {
            key: 'menus',
            label: '菜单权限',
            children: (
              <Table<MenuTreeItem>
                rowKey="id"
                loading={loading}
                columns={columns}
                dataSource={menus}
                expandable={{ defaultExpandAllRows: true }}
                pagination={false}
                scroll={{ x: 1200 }}
              />
            ),
          },
          {
            key: 'apis',
            label: '接口权限',
            children: apiGroups.length ? (
              <Space direction="vertical" size={16} className="w-full">
                {apiGroups.map((group) => (
                  <Card key={group.group_name} size="small" title={group.group_name}>
                    <Table
                      rowKey="id"
                      size="small"
                      pagination={false}
                      dataSource={group.permissions}
                      columns={[
                        { title: '名称', dataIndex: 'name', key: 'name' },
                        { title: '方法', dataIndex: 'method', key: 'method', width: 100 },
                        { title: '路径', dataIndex: 'api_path', key: 'api_path' },
                        { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
                      ]}
                    />
                  </Card>
                ))}
              </Space>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无接口权限数据" />
            ),
          },
          {
            key: 'data',
            label: '数据权限',
            children: dataScopes.length ? (
              <Table<DataScopeOption>
                rowKey="scope"
                pagination={false}
                dataSource={dataScopes}
                columns={[
                  { title: '范围编码', dataIndex: 'scope', key: 'scope', width: 180 },
                  {
                    title: '资源类型',
                    dataIndex: 'resource_types',
                    key: 'resource_types',
                    render: (values: string[]) =>
                      values.map((value) => <Tag key={value}>{value}</Tag>),
                  },
                ]}
              />
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据权限配置" />
            ),
          },
        ]}
      />
      <Drawer
        title={editingMenu ? '编辑菜单权限' : '新建菜单权限'}
        width={460}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Button type="primary" loading={saving} onClick={() => void saveMenu()}>
            保存
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ sort_order: 0, status: 'ENABLED' }}
        >
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入菜单名称' }]}
          >
            <Input placeholder="请输入菜单名称" />
          </Form.Item>
          <Form.Item name="parent_id" label="父级菜单">
            <Select
              allowClear
              placeholder="一级菜单可留空"
              options={flattenMenus(menus).map((item) => ({
                label: `${item.name}${item.path ? ` (${item.path})` : ''}`,
                value: item.id,
              }))}
            />
          </Form.Item>
          <Form.Item name="path" label="路由路径">
            <Input placeholder="如 /users" />
          </Form.Item>
          <Form.Item name="component" label="组件路径">
            <Input placeholder="如 pages/users/index" />
          </Form.Item>
          <Form.Item name="icon" label="图标">
            <Input placeholder="如 TeamOutlined" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber className="w-full" min={0} />
          </Form.Item>
          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select
              options={[
                { label: '启用', value: 'ENABLED' },
                { label: '禁用', value: 'DISABLED' },
              ]}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </PageCard>
  )
}
