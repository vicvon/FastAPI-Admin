import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Drawer,
  Form,
  Input,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useCallback, useEffect, useState } from 'react'

import { PageCard } from '../components/page-card'
import { StatusTag } from '../components/status-tag'
import { roleApi, userApi } from '../features/services/api'
import type { RoleItem, UserItem } from '../types/admin'

export function UsersPage() {
  const { message } = AntdApp.useApp()
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<UserItem[]>([])
  const [roles, setRoles] = useState<RoleItem[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [assignOpen, setAssignOpen] = useState(false)
  const [editing, setEditing] = useState<UserItem | null>(null)
  const [assigning, setAssigning] = useState<UserItem | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<{
    username: string
    email: string
    full_name?: string
    password?: string
    is_active?: boolean
  }>()
  const [assignForm] = Form.useForm<{ role_ids: string[] }>()

  const loadUsers = useCallback(
    async (nextPage = page, nextPageSize = pageSize) => {
      setLoading(true)
      try {
        const [userData, roleData] = await Promise.all([
          userApi.list({ page: nextPage, page_size: nextPageSize }),
          roleApi.list(),
        ])
        setUsers(userData.items)
        setTotal(userData.total)
        setPage(userData.page)
        setPageSize(userData.page_size)
        setRoles(roleData)
      } catch (error) {
        message.error(error instanceof Error ? error.message : '加载用户失败')
      } finally {
        setLoading(false)
      }
    },
    [message, page, pageSize],
  )

  useEffect(() => {
    void loadUsers(1, 10)
  }, [loadUsers])

  const columns: ColumnsType<UserItem> = [
    { title: '用户名', dataIndex: 'username', key: 'username', width: 160 },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 220 },
    {
      title: '姓名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (value) => value || '--',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (value: boolean) => (
        <StatusTag enabled={value} activeText="正常" inactiveText="禁用" />
      ),
    },
    {
      title: '角色',
      dataIndex: 'roles',
      key: 'roles',
      render: (value: UserItem['roles']) =>
        value?.length ? (
          value.map((role) => <Tag key={role.id}>{role.name}</Tag>)
        ) : (
          <Typography.Text type="secondary">未分配</Typography.Text>
        ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Button type="link" onClick={() => openAssign(record)}>
            分配角色
          </Button>
        </Space>
      ),
    },
  ]

  const openEdit = (record: UserItem) => {
    setEditing(record)
    form.setFieldsValue({
      username: record.username,
      email: record.email,
      full_name: record.full_name || undefined,
      is_active: record.is_active,
    })
    setDrawerOpen(true)
  }

  const openAssign = (record: UserItem) => {
    setAssigning(record)
    assignForm.setFieldsValue({
      role_ids: record.roles?.map((item) => item.id) || [],
    })
    setAssignOpen(true)
  }

  const saveUser = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editing) {
        await userApi.update(editing.id, values)
        message.success('用户更新成功')
      } else {
        await userApi.create({
          username: values.username,
          email: values.email,
          full_name: values.full_name,
          password: values.password || '',
        })
        message.success('用户创建成功')
      }
      setDrawerOpen(false)
      setEditing(null)
      await loadUsers()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '用户保存失败')
    } finally {
      setSaving(false)
    }
  }

  const saveAssign = async () => {
    if (!assigning) return
    const values = await assignForm.validateFields()
    setSaving(true)
    try {
      await userApi.assignRoles(assigning.id, values.role_ids)
      message.success('角色分配成功')
      setAssignOpen(false)
      await loadUsers()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '角色分配失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageCard
      title="用户管理"
      description="对接 /api/v1/users 接口，支持分页查看、创建、编辑与角色分配。"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void loadUsers()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null)
              form.resetFields()
              form.setFieldsValue({ is_active: true })
              setDrawerOpen(true)
            }}
          >
            新建用户
          </Button>
        </Space>
      }
    >
      <Table<UserItem>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={users}
        scroll={{ x: 1100 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          onChange: (nextPage, nextPageSize) => {
            void loadUsers(nextPage, nextPageSize)
          },
        }}
      />
      <Drawer
        title={editing ? '编辑用户' : '新建用户'}
        width={440}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
        extra={
          <Button type="primary" loading={saving} onClick={() => void saveUser()}>
            保存
          </Button>
        }
      >
        <Form form={form} layout="vertical" initialValues={{ is_active: true }}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="full_name" label="姓名">
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={editing ? [] : [{ required: true, message: '请输入初始密码' }]}
          >
            <Input.Password placeholder={editing ? '留空则不修改' : '请输入初始密码'} />
          </Form.Item>
          {editing ? (
            <Form.Item name="is_active" label="是否启用" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          ) : null}
        </Form>
      </Drawer>
      <Drawer
        title={assigning ? `为 ${assigning.username} 分配角色` : '分配角色'}
        width={420}
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        destroyOnClose
        extra={
          <Button type="primary" loading={saving} onClick={() => void saveAssign()}>
            保存配置
          </Button>
        }
      >
        <Form form={assignForm} layout="vertical">
          <Form.Item
            name="role_ids"
            label="角色列表"
            rules={[{ required: true, message: '请至少选择一个角色' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择角色"
              options={roles.map((role) => ({
                label: `${role.name} (${role.code})`,
                value: role.id,
              }))}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </PageCard>
  )
}
