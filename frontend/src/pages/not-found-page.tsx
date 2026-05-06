import { Button, Result } from 'antd'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Result
        status="404"
        title="404"
        subTitle="当前页面不存在或已被移除。"
        extra={
          <Button type="primary">
            <Link to="/">返回首页</Link>
          </Button>
        }
      />
    </div>
  )
}
