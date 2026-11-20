import { useAuth } from '../../contexts/AuthContext'
import { TopBar } from '../../components/layout/TopBar'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from '../../components/ui'
import { ShieldCheck, Store, Utensils } from 'lucide-react'

export function AdminDashboardPage() {
  const { user, restaurante, logout } = useAuth()

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col">
      <TopBar
        restaurantName={restaurante?.nome || 'Nenhum Restaurante Selecionado'}
        role="dono"
        userName={user?.nome}
        onLogout={logout}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Painel Administrativo</h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Visão geral da gestão multi-restaurante e controle financeiro.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Sessão Autenticada</CardTitle>
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
              </div>
              <CardDescription>Perfil ativo com privilégio total</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-xs space-y-1">
                <p><span className="text-zinc-500">Gestor:</span> {user?.nome || 'Dono'}</p>
                <p><span className="text-zinc-500">E-mail:</span> {user?.email}</p>
                <p><span className="text-zinc-500">Permissão:</span> <Badge variant="zinc" size="sm">Dono</Badge></p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Restaurante Ativo</CardTitle>
                <Store className="w-4 h-4 text-red-600" />
              </div>
              <CardDescription>Contexto multi-tenant selecionado</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-xs space-y-1">
                <p><span className="text-zinc-500">Nome:</span> {restaurante?.nome || 'Não configurado'}</p>
                <p><span className="text-zinc-500">Slug:</span> {restaurante?.slug || '—'}</p>
                <p><span className="text-zinc-500">Status:</span> <Badge variant="emerald" size="sm" withDot>Operacional</Badge></p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Módulos do Sistema</CardTitle>
                <Utensils className="w-4 h-4 text-zinc-400" />
              </div>
              <CardDescription>Próximas entregas da esteira</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="sky" size="sm">Cardápio (#52)</Badge>
                <Badge variant="amber" size="sm">Comandas (#53)</Badge>
                <Badge variant="emerald" size="sm">Fechamento (#54)</Badge>
                <Badge variant="red" size="sm">Financeiro (#56)</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Ambiente Operacional Seguro</CardTitle>
            <CardDescription>
              Rotas administrativas protegidas com autenticação JWT e isolamento multi-tenant garantido.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
              O fluxo de autenticação do Dono valida o token via interceptor Axios com restauração automática em <code>/api/v1/auth/me</code>. Qualquer acesso sem privilégio de dono a este módulo é bloqueado e redirecionado pelo <code>ProtectedRoute</code>.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
