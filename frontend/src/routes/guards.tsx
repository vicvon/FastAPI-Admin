import { Spin } from 'antd'
import type { PropsWithChildren } from 'react'
import { Navigate, useLocation } from 'react-router-dom'

import { useAuth } from '../features/auth/auth-context'

export function RequireAuth({ children }: PropsWithChildren) {
  const { authenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spin size="large" />
      </div>
    )
  }

  if (!authenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}

export function PublicOnly({ children }: PropsWithChildren) {
  const { authenticated, loading } = useAuth()

  if (!loading && authenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
