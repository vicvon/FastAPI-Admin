import type { TreeDataNode } from 'antd'
import { Space, Tag } from 'antd'

import type { LabelTreeNode, MenuTreeItem } from '../types/admin'

export function flattenMenus(nodes: MenuTreeItem[]): MenuTreeItem[] {
  return nodes.flatMap((node) => [node, ...flattenMenus(node.children || [])])
}

export function flattenLabels(nodes: LabelTreeNode[]): LabelTreeNode[] {
  return nodes.flatMap((node) => [node, ...flattenLabels(node.children || [])])
}

export function toMenuTreeNodes(nodes: MenuTreeItem[]): TreeDataNode[] {
  return nodes.map((node) => ({
    key: node.id,
    title: `${node.name}${node.path ? ` (${node.path})` : ''}`,
    children: toMenuTreeNodes(node.children || []),
  }))
}

export function toLabelTreeNodes(nodes: LabelTreeNode[]): TreeDataNode[] {
  return nodes.map((node) => ({
    key: node.id,
    title: (
      <Space>
        <span>{node.name}</span>
        <Tag>{`L${node.level}`}</Tag>
      </Space>
    ),
    children: toLabelTreeNodes(node.children || []),
  }))
}
