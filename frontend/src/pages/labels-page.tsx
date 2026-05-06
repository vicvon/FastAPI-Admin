import {
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import {
  App as AntdApp,
  Button,
  Drawer,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tree,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { PageCard } from '../components/page-card'
import { StatusTag } from '../components/status-tag'
import { labelApi } from '../features/services/api'
import { toLabelTreeNodes } from '../lib/tree'
import type { LabelItem, LabelTreeNode } from '../types/admin'

export function LabelsPage() {
  const { message } = AntdApp.useApp()
  const [loading, setLoading] = useState(false)
  const [labels, setLabels] = useState<LabelItem[]>([])
  const [tree, setTree] = useState<LabelTreeNode[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [moveOpen, setMoveOpen] = useState(false)
  const [editing, setEditing] = useState<LabelItem | null>(null)
  const [moving, setMoving] = useState<LabelItem | null>(null)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm<{
    name: string
    parent_id: string
    sort_order: number
    enabled: boolean
    description?: string
  }>()
  const [moveForm] = Form.useForm<{ new_parent_id: string }>()

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [listData, treeData] = await Promise.all([labelApi.list(), labelApi.tree()])
      setLabels(listData)
      setTree(treeData)
    } catch (error) {
      message.error(error instanceof Error ? error.message : '标签数据加载失败')
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const parentOptions = useMemo(
    () => [
      { id: '0', name: '一级标签' },
      ...labels.map((item) => ({ id: item.id, name: item.name })),
    ],
    [labels],
  )

  const columns: ColumnsType<LabelItem> = [
    { title: '标签名称', dataIndex: 'name', key: 'name', width: 160 },
    { title: '层级', dataIndex: 'level', key: 'level', width: 80 },
    { title: '父节点', dataIndex: 'parent_id', key: 'parent_id', width: 140 },
    { title: '路径', dataIndex: 'path', key: 'path', width: 220 },
    { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (value: boolean) => <StatusTag enabled={value} />,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (value: string) => dayjs(value).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            onClick={() => {
              setEditing(record)
              form.setFieldsValue({
                name: record.name,
                parent_id: record.parent_id,
                sort_order: record.sort_order,
                enabled: record.enabled,
                description: record.description || undefined,
              })
              setDrawerOpen(true)
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            icon={<SwapOutlined />}
            onClick={() => {
              setMoving(record)
              moveForm.setFieldsValue({ new_parent_id: record.parent_id })
              setMoveOpen(true)
            }}
          >
            移动
          </Button>
          <Popconfirm
            title="确认删除该标签吗？"
            onConfirm={() => void deleteLabel(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const saveLabel = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      if (editing) {
        await labelApi.update(editing.id, values)
        message.success('标签更新成功')
      } else {
        await labelApi.create(values)
        message.success('标签创建成功')
      }
      setDrawerOpen(false)
      setEditing(null)
      await loadData()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '标签保存失败')
    } finally {
      setSaving(false)
    }
  }

  const moveLabel = async () => {
    if (!moving) return
    const values = await moveForm.validateFields()
    setSaving(true)
    try {
      await labelApi.move(moving.id, values.new_parent_id)
      message.success('标签移动成功')
      setMoveOpen(false)
      await loadData()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '标签移动失败')
    } finally {
      setSaving(false)
    }
  }

  const deleteLabel = async (labelId: string) => {
    try {
      await labelApi.remove(labelId)
      message.success('标签删除成功')
      await loadData()
    } catch (error) {
      message.error(error instanceof Error ? error.message : '标签删除失败')
    }
  }

  return (
    <PageCard
      title="标签管理"
      description="对接 label_manager 模块，支持树形查看、创建、编辑、移动与删除标签。"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void loadData()}>
            刷新
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditing(null)
              form.resetFields()
              form.setFieldsValue({ parent_id: '0', sort_order: 0, enabled: true })
              setDrawerOpen(true)
            }}
          >
            新建标签
          </Button>
        </Space>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
          <Typography.Title level={5}>标签树</Typography.Title>
          <Tree treeData={toLabelTreeNodes(tree)} defaultExpandAll showLine />
        </div>
        <Table<LabelItem>
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={labels}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1300 }}
        />
      </div>
      <Drawer
        title={editing ? '编辑标签' : '新建标签'}
        width={420}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        extra={
          <Button type="primary" loading={saving} onClick={() => void saveLabel()}>
            保存
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ parent_id: '0', sort_order: 0, enabled: true }}
        >
          <Form.Item
            name="name"
            label="标签名称"
            rules={[{ required: true, message: '请输入标签名称' }]}
          >
            <Input placeholder="请输入标签名称" />
          </Form.Item>
          {!editing ? (
            <Form.Item
              name="parent_id"
              label="父标签"
              rules={[{ required: true, message: '请选择父标签' }]}
            >
              <Select
                options={parentOptions.map((option) => ({
                  label: option.name,
                  value: option.id,
                }))}
              />
            </Form.Item>
          ) : null}
          <Form.Item name="sort_order" label="排序">
            <InputNumber className="w-full" min={0} />
          </Form.Item>
          <Form.Item name="enabled" label="是否启用" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={4} placeholder="请输入标签描述" />
          </Form.Item>
        </Form>
      </Drawer>
      <Drawer
        title={moving ? `移动标签 - ${moving.name}` : '移动标签'}
        width={380}
        open={moveOpen}
        onClose={() => setMoveOpen(false)}
        extra={
          <Button type="primary" loading={saving} onClick={() => void moveLabel()}>
            确认移动
          </Button>
        }
      >
        <Form form={moveForm} layout="vertical">
          <Form.Item
            name="new_parent_id"
            label="新父标签"
            rules={[{ required: true, message: '请选择新父标签' }]}
          >
            <Select
              options={parentOptions
                .filter((item) => item.id !== moving?.id)
                .map((option) => ({
                  label: option.name,
                  value: option.id,
                }))}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </PageCard>
  )
}
