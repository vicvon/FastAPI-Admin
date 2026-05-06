import {
  LockOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, App as AntdApp, Button, Card, Form, Input, Typography } from 'antd'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../features/auth/auth-context'

export function LoginPage() {
  const { message } = AntdApp.useApp()
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const onFinish = async (values: { username: string; password: string }) => {
    setSubmitting(true)
    setErrorMessage('')
    try {
      await login(values)
      message.success('登录成功')
      navigate((location.state as { from?: string } | undefined)?.from || '/', {
        replace: true,
      })
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '登录失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.22),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(14,165,233,0.18),transparent_30%)]" />
      <div className="relative grid w-full max-w-6xl gap-8 lg:grid-cols-[1.1fr_480px]">
        <div className="hidden rounded-[32px] border border-white/60 bg-slate-950 p-10 text-slate-50 shadow-2xl lg:flex lg:flex-col lg:justify-between">
          <div className="space-y-6">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
              <SafetyCertificateOutlined className="text-2xl text-sky-300" />
            </div>
            <div className="space-y-3">
              <Typography.Title level={1} className="!mb-0 !text-slate-50">
                企业级后台管理前端
              </Typography.Title>
              <Typography.Paragraph className="!mb-0 !text-slate-300">
                基于 React、Ant Design 与 Tailwind 构建，覆盖用户、角色、菜单权限、接口权限、数据权限与标签管理。
              </Typography.Paragraph>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              ['RBAC 权限', '对齐后端 admin 模块接口'],
              ['统一鉴权', 'Bearer Token + 用户态恢复'],
              ['低成本扩展', '首版已经具备后台常用信息架构'],
              ['快速部署', 'Vite 开发代理直连后端'],
            ].map(([title, desc]) => (
              <div
                key={title}
                className="rounded-2xl border border-white/10 bg-white/5 p-4"
              >
                <div className="font-medium">{title}</div>
                <div className="mt-2 text-sm text-slate-300">{desc}</div>
              </div>
            ))}
          </div>
        </div>
        <Card className="border-white/70 bg-white/85 shadow-2xl backdrop-blur">
          <div className="mb-8">
            <Typography.Title level={2} className="!mb-2">
              登录系统
            </Typography.Title>
            <Typography.Text type="secondary">
              默认可使用后端初始化的管理员账号进行登录。
            </Typography.Text>
          </div>
          {errorMessage ? (
            <Alert showIcon type="error" message={errorMessage} className="mb-6" />
          ) : null}
          <Form
            layout="vertical"
            onFinish={onFinish}
            initialValues={{ username: 'admin' }}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input size="large" prefix={<UserOutlined />} placeholder="请输入用户名" />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                size="large"
                prefix={<LockOutlined />}
                placeholder="请输入密码"
              />
            </Form.Item>
            <Button
              htmlType="submit"
              type="primary"
              size="large"
              block
              loading={submitting}
            >
              登录后台
            </Button>
          </Form>
          <div className="mt-6 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
            建议首次登录后立即修改默认密码，并根据实际业务配置角色与数据权限。
          </div>
        </Card>
      </div>
    </div>
  )
}
