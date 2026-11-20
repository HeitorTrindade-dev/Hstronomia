import { useAuth } from '../../contexts/AuthContext'
import { TopBar } from '../../components/layout/TopBar'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from '../../components/ui'
import { ClipboardList, Users } from 'lucide-react'

export function GarcomDashboardPage() {
  const { restaurante, logout } = useAuth()

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col">
      <TopBar
        restaurantName={restaurante?.nome || 'Terminal do Garçom'}
        role="garcom"
        onLogout={logout}
      />

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Atendimento e Mesas</h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Sessão operacional autenticada por PIN no restaurante: <strong>{restaurante?.nome}</strong>
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Perfil Garçom Ativo</CardTitle>
                <Users className="w-4 h-4 text-sky-600" />
              </div>
              <CardDescription>Acesso rápido mobile-first</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-xs space-y-1">
                <p><span className="text-zinc-500">Restaurante:</span> {restaurante?.nome}</p>
                <p><span className="text-zinc-500">Slug:</span> {restaurante?.slug}</p>
                <p><span className="text-zinc-500">Nível:</span> <Badge variant="sky" size="sm">Operacional (Garçom)</Badge></p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Módulo de Mesas e Pedidos</CardTitle>
                <ClipboardList className="w-4 h-4 text-zinc-400" />
              </div>
              <CardDescription>A ser implementado na Issue #53</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Abertura ágil de comandas, catálogo de itens do cardápio e congelamento de preços históricos.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
