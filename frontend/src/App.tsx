import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ProtectedRoute } from './components/layout'
import { Skeleton } from './components/ui'

// Páginas de Autenticação
import { LoginDono } from './pages/auth/LoginDono'
import { CadastroDono } from './pages/auth/CadastroDono'
import { AcessoOperacional } from './pages/auth/AcessoOperacional'

// Painéis Operacionais e Administrativos
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage'
import { GarcomDashboardPage } from './pages/garcom/GarcomDashboardPage'
import { CozinhaKdsPage } from './pages/cozinha/CozinhaKdsPage'
import { DesignSystemPage } from './pages/DesignSystemPage'
import { NotFoundPage } from './pages/NotFoundPage'

function RootRedirect() {
  const { isAuthenticated, isLoading, role } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-zinc-50 dark:bg-zinc-950">
        <div className="w-full max-w-sm space-y-3">
          <Skeleton className="h-8 w-48 mx-auto" />
          <Skeleton className="h-4 w-32 mx-auto" />
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role === 'dono') {
    return <Navigate to="/admin" replace />
  }
  if (role === 'garcom') {
    return <Navigate to="/garcom" replace />
  }
  if (role === 'cozinha') {
    return <Navigate to="/cozinha" replace />
  }

  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rota Raiz Inteligente */}
          <Route path="/" element={<RootRedirect />} />

          {/* Rotas Públicas de Autenticação */}
          <Route path="/login" element={<LoginDono />} />
          <Route path="/cadastrar" element={<CadastroDono />} />
          <Route path="/acesso/:slug" element={<AcessoOperacional />} />
          <Route path="/acesso" element={<Navigate to="/acesso/cantina-famiglia" replace />} />

          {/* Vitrine do Design System */}
          <Route path="/design-system" element={<DesignSystemPage />} />

          {/* Rotas Protegidas - Dono */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={['dono']}>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Rotas Protegidas - Garçom */}
          <Route
            path="/garcom/*"
            element={
              <ProtectedRoute allowedRoles={['garcom']}>
                <GarcomDashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Rotas Protegidas - Cozinha KDS */}
          <Route
            path="/cozinha/*"
            element={
              <ProtectedRoute allowedRoles={['cozinha']}>
                <CozinhaKdsPage />
              </ProtectedRoute>
            }
          />

          {/* Página 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
