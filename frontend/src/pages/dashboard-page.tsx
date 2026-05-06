import {
  ApiOutlined,
  DashboardOutlined,
  MenuOutlined,
  TagsOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, Col, List, Row, Space, Spin, Typography } from 'antd'
import { useEffect, useState } from 'react'

import { PageCard } from '../components/page-card'
import { StatCard } from '../components/stat-card'
import { labelApi, permissionApi, roleApi, userApi } from '../features/services/api'
import { flattenLabels, flattenMenus } from '../lib/tree'
import type { LabelTreeNode } from '../types/admin'

export function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [metrics, setMetrics] = useState({
    users: 0,
    roles: 0,
    menus: 0,
    apiPermissions: 0,
    dataScopes: 0,
    labels: 0,
  })
  const [recentLabels, setRecentLabels] = useState<LabelTreeNode[]>([])

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError('')
      try {
        const [users, roles, menus, apis, dataScopes, labels] = await Promise.all([
          userApi.list({ page: 1, page_size: 5 }),
          roleApi.list(),
          permissionApi.getMenus(),
          permissionApi.getApiPermissions(),
          permissionApi.getDataScopeOptions(),
          labelApi.tree(),
        ])
        const labelList = flattenLabels(labels)
        setMetrics({
          users: users.total,
          roles: roles.length,
          menus: flattenMenus(menus.menus).length,
          apiPermissions: apis.api_groups.reduce(
            (sum, group) => sum + group.permissions.length,
            0,
          ),
          dataScopes: dataScopes.data_scope_options.length,
          labels: labelList.length,
        })
        setRecentLabels(labelList.slice(0, 5))
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : '概览加载失败')
      } finally {
        setLoading(false)
      }
    }
    void run()
  }, [])

  return (
    <Space direction="vertical" size={24} className="w-full">
      <div>
        <Typography.Title level={3} className="!mb-2">
          业务概览
        </Typography.Title>
        <Typography.Text type="secondary">
          基于后端真实接口统计关键实体，帮助快速验证后台基础能力。
        </Typography.Text>
      </div>
      {error ? <Alert type="error" showIcon message={error} /> : null}
      {loading ? (
        <div className="flex items-center justify-center py-24">
          <Spin size="large" />
        </div>
      ) : (
        <>
          <Row gutter={[16, 16]}>
            {[
              ['用户总数', metrics.users, <TeamOutlined />],
              ['角色数量', metrics.roles, <UserOutlined />],
              ['菜单节点', metrics.menus, <MenuOutlined />],
              ['接口权限', metrics.apiPermissions, <ApiOutlined />],
              ['数据权限集', metrics.dataScopes, <DashboardOutlined />],
              ['标签节点', metrics.labels, <TagsOutlined />],
            ].map(([title, value, icon]) => (
              <Col key={String(title)} xs={24} sm={12} xl={8}>
                <StatCard title={String(title)} value={Number(value)} prefix={icon} />
              </Col>
            ))}
          </Row>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={16}>
              <PageCard
                title="前端落地说明"
                description="当前版本已具备登录、主导航、数据概览与核心 CRUD 页面。"
              >
                <List
                  dataSource={[
                    '用户管理：分页查看、创建、编辑、分配角色。',
                    '角色管理：维护角色并统一配置菜单、接口与数据权限。',
                    '权限中心：查看并维护菜单权限、接口权限、数据权限选项。',
                    '标签管理：对接 label_manager 模块实现树形维护。',
                  ]}
                  renderItem={(item) => <List.Item>{item}</List.Item>}
                />
              </PageCard>
            </Col>
            <Col xs={24} xl={8}>
              <PageCard title="最近标签节点" description="展示标签树前几个节点">
                <List
                  dataSource={recentLabels}
                  locale={{ emptyText: '暂无标签数据' }}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        title={item.name}
                        description={`层级 ${item.level} · 路径 ${item.path}`}
                      />
                    </List.Item>
                  )}
                />
              </PageCard>
            </Col>
          </Row>
        </>
      )}
    </Space>
  )
}
