import {
  ApiOutlined,
  DashboardOutlined,
  LogoutOutlined,
  MenuOutlined,
  TagsOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import { Avatar, Breadcrumb, Dropdown, Layout, Menu, Space, Typography } from 'antd'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../features/auth/auth-context'

const { Header, Sider, Content } = Layout

function getSelectedKey(pathname: string) {
  if (pathname.startsWith('/users')) return '/users'
  if (pathname.startsWith('/roles')) return '/roles'
  if (pathname.startsWith('/permissions')) return '/permissions'
  if (pathname.startsWith('/apis')) return '/apis'
  if (pathname.startsWith('/labels')) return '/labels'
  return '/'
}

export function AdminLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const selectedKey = getSelectedKey(location.pathname)

  const userMenu: MenuProps['items'] = [
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      onClick: () => {
        void logout().then(() => navigate('/login'))
      },
    },
  ]

  return (
    <Layout>
      <Sider
        theme="light"
        width={248}
        className="border-r border-slate-200 bg-white/90 backdrop-blur"
      >
        <div className="flex h-16 items-center gap-3 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
            FA
          </div>
          <div>
            <Typography.Text strong>FastAPI Admin</Typography.Text>
            <Typography.Paragraph type="secondary" className="!mb-0 text-xs">
              React + AntD 控制台
            </Typography.Paragraph>
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={[
            { key: '/', icon: <DashboardOutlined />, label: <Link to="/">仪表盘</Link> },
            { key: '/users', icon: <TeamOutlined />, label: <Link to="/users">用户管理</Link> },
            { key: '/roles', icon: <UserOutlined />, label: <Link to="/roles">角色管理</Link> },
            { key: '/permissions', icon: <MenuOutlined />, label: <Link to="/permissions">权限中心</Link> },
            { key: '/apis', icon: <ApiOutlined />, label: <Link to="/apis">接口权限</Link> },
            { key: '/labels', icon: <TagsOutlined />, label: <Link to="/labels">标签管理</Link> },
          ]}
          className="px-3"
        />
      </Sider>
      <Layout>
        <Header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-6 backdrop-blur">
          <div>
            <Typography.Title level={4} className="!mb-0">
              后台管理系统
            </Typography.Title>
            <Typography.Text type="secondary">
              对齐后端现有 admin 与 label_manager 能力
            </Typography.Text>
          </div>
          <Dropdown menu={{ items: userMenu }} trigger={['click']}>
            <Space className="cursor-pointer rounded-full border border-slate-200 bg-white px-3 py-2">
              <Avatar icon={<UserOutlined />} />
              <div className="leading-tight">
                <Typography.Text strong>
                  {user?.full_name || user?.username || '管理员'}
                </Typography.Text>
                <Typography.Paragraph type="secondary" className="!mb-0 text-xs">
                  {user?.roles?.map((role) => role.name).join(' / ') || '未分配角色'}
                </Typography.Paragraph>
              </div>
            </Space>
          </Dropdown>
        </Header>
        <Content className="p-6">
          <div className="mx-auto flex max-w-7xl flex-col gap-6">
            <Breadcrumb
              items={location.pathname
                .split('/')
                .filter(Boolean)
                .map((part) => ({ title: part }))}
            />
            <Outlet />
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}
