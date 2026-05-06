import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AuthProvider } from '../features/auth/auth-context'
import { AdminLayout } from '../layouts/admin-layout'
import { DashboardPage } from '../pages/dashboard-page'
import { LabelsPage } from '../pages/labels-page'
import { LoginPage } from '../pages/login-page'
import { NotFoundPage } from '../pages/not-found-page'
import { PermissionsPage } from '../pages/permissions-page'
import { RolesPage } from '../pages/roles-page'
import { UsersPage } from '../pages/users-page'
import { PublicOnly, RequireAuth } from './guards'

export function AppRoutes() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicOnly>
                <LoginPage />
              </PublicOnly>
            }
          />
          <Route
            path="/"
            element={
              <RequireAuth>
                <AdminLayout />
              </RequireAuth>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="roles" element={<RolesPage />} />
            <Route path="permissions" element={<PermissionsPage />} />
            <Route path="apis" element={<PermissionsPage defaultTab="apis" />} />
            <Route path="labels" element={<LabelsPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
