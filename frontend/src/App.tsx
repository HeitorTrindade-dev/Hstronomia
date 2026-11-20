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
import { Restaurantes } from './pages/admin/Restaurantes'
import { Cardapio } from './pages/admin/Cardapio'
import { Financeiro } from './pages/admin/Financeiro'
import { Mesas } from './pages/garcom/Mesas'
import { ComandaDetalhe } from './pages/garcom/ComandaDetalhe'
import { KDS } from './pages/cozinha/KDS'
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
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['dono']}>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/cardapio"
            element={
              <ProtectedRoute allowedRoles={['dono']}>
                <Cardapio />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/restaurantes"
            element={
              <ProtectedRoute allowedRoles={['dono']}>
                <Restaurantes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/financeiro"
            element={
              <ProtectedRoute allowedRoles={['dono']}>
                <Financeiro />
              </ProtectedRoute>
            }
          />

          {/* Rotas Protegidas - Atendimento / Salão (Garçom ou Dono) */}
          <Route path="/garcom" element={<Navigate to="/garcom/mesas" replace />} />
          <Route
            path="/garcom/mesas"
            element={
              <ProtectedRoute allowedRoles={['dono', 'garcom']}>
                <Mesas />
              </ProtectedRoute>
            }
          />
          <Route
            path="/garcom/comandas/:id"
            element={
              <ProtectedRoute allowedRoles={['dono', 'garcom']}>
                <ComandaDetalhe />
              </ProtectedRoute>
            }
          />

          {/* Rotas Protegidas - Cozinha KDS (Cozinha ou Dono) */}
          <Route
            path="/cozinha"
            element={
              <ProtectedRoute allowedRoles={['dono', 'cozinha']}>
                <KDS />
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
