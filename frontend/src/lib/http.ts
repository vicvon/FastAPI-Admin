import axios from 'axios'

import type { ApiResponse } from '../types/api'
import { clearTokens, getAccessToken } from './storage'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearTokens()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export async function unwrapResponse<T>(
  promise: Promise<{ data: ApiResponse<T> }>,
): Promise<T> {
  const response = await promise
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '请求失败')
  }
  return response.data.data as T
}
