import { Tag } from 'antd'

export function StatusTag({
  enabled,
  activeText = '启用',
  inactiveText = '停用',
}: {
  enabled?: boolean
  activeText?: string
  inactiveText?: string
}) {
  return (
    <Tag color={enabled ? 'success' : 'default'}>
      {enabled ? activeText : inactiveText}
    </Tag>
  )
}
