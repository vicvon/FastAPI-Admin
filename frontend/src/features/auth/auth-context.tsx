import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { PropsWithChildren } from 'react'

import { authApi, userApi } from '../services/api'
import type { UserMe } from '../../types/admin'
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../../lib/storage'

interface AuthContextValue {
  user: UserMe | null
  loading: boolean
  authenticated: boolean
  login: (payload: { username: string; password: string }) => Promise<void>
  logout: () => Promise<void>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<UserMe | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshProfile = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const profile = await userApi.getCurrentUser()
      setUser(profile)
    } catch {
      clearTokens()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshProfile()
  }, [refreshProfile])

  const login = useCallback(async (payload: { username: string; password: string }) => {
    const tokens = await authApi.login(payload.username, payload.password)
    setTokens(tokens.access_token, tokens.refresh_token)
    const profile = await userApi.getCurrentUser()
    setUser(profile)
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = getRefreshToken()
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken)
      }
    } finally {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      authenticated: Boolean(user && getAccessToken()),
      login,
      logout,
      refreshProfile,
    }),
    [user, loading, login, logout, refreshProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth 必须在 AuthProvider 中使用')
  }
  return context
}
