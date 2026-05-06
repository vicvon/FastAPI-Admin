import { Card, Statistic } from 'antd'
import type { ReactNode } from 'react'

export function StatCard({
  title,
  value,
  prefix,
}: {
  title: string
  value: number | string
  prefix?: ReactNode
}) {
  return (
    <Card className="h-full shadow-sm">
      <Statistic title={title} value={value} prefix={prefix} />
    </Card>
  )
}
