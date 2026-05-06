import { Card, Space, Typography } from 'antd'
import type { ReactNode } from 'react'

export function PageCard({
  title,
  description,
  extra,
  children,
}: {
  title: string
  description?: string
  extra?: ReactNode
  children: ReactNode
}) {
  return (
    <Card
      title={
        <Space direction="vertical" size={2}>
          <Typography.Text strong>{title}</Typography.Text>
          {description ? (
            <Typography.Text type="secondary">{description}</Typography.Text>
          ) : null}
        </Space>
      }
      extra={extra}
      className="shadow-sm"
    >
      {children}
    </Card>
  )
}
