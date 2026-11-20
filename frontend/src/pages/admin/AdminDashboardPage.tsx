import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { TopBar } from '../../components/layout/TopBar'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge, Button } from '../../components/ui'
import { ShieldCheck, Store, Utensils, ArrowRight, BookOpen, KeyRound } from 'lucide-react'

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
            Visão geral da gestão multi-restaurante e controle operacional.
          </p>
        </div>

        {/* Cards de Métricas e Contexto */}
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
              <CardDescription>Status das entregas da esteira</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex flex-wrap gap-1.5">
                <Badge variant="emerald" size="sm" withDot>Cardápio (#52)</Badge>
                <Badge variant="emerald" size="sm" withDot>Restaurantes & PINs (#52)</Badge>
                <Badge variant="amber" size="sm">Comandas (#53)</Badge>
                <Badge variant="amber" size="sm">Fechamento (#54)</Badge>
                <Badge variant="zinc" size="sm">Financeiro (#56)</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Atalhos Rápidos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-red-600" />
                  <CardTitle>Gestão do Cardápio</CardTitle>
                </div>
                <Link to="/admin/cardapio">
                  <Button variant="ghost" size="sm">
                    Acessar <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
              <CardDescription>
                Adicione novos pratos, altere preços, pause itens no salão ou realize desativação segura (soft-delete).
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-5 h-5 text-red-600" />
                  <CardTitle>Restaurantes & PINs</CardTitle>
                </div>
                <Link to="/admin/restaurantes">
                  <Button variant="ghost" size="sm">
                    Acessar <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                </Link>
              </div>
              <CardDescription>
                Cadastre novos estabelecimentos, selecione o restaurante ativo e rotacione os PINs de Garçom e Cozinha.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>
    </div>
  )
}
