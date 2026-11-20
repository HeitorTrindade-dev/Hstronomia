import { useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { TopBar } from '../../components/layout/TopBar'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Badge } from '../../components/ui'
import { Flame, Clock } from 'lucide-react'

export function CozinhaKdsPage() {
  const { restaurante, logout } = useAuth()

  // Força Dark Mode na Cozinha KDS conforme especificação de estilos.md
  useEffect(() => {
    document.documentElement.classList.add('dark')
  }, [])

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col">
      <TopBar
        restaurantName={restaurante?.nome || 'Cozinha KDS'}
        role="cozinha"
        onLogout={logout}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Flame className="w-5 h-5 text-amber-500" /> Cozinha KDS (Kitchen Display System)
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Fila de preparo em tempo real para o restaurante: <strong>{restaurante?.nome}</strong>
            </p>
          </div>

          <Badge variant="amber" size="md" withDot>
            Terminal Operacional Ativo
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader className="border-zinc-800">
              <div className="flex items-center justify-between">
                <CardTitle>Sessão de Cozinha Conectada</CardTitle>
                <Clock className="w-4 h-4 text-amber-400" />
              </div>
              <CardDescription>Acesso operacional restrito aos pedidos e status KDS</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-xs space-y-1">
                <p><span className="text-zinc-500">Restaurante:</span> {restaurante?.nome}</p>
                <p><span className="text-zinc-500">Slug:</span> {restaurante?.slug}</p>
                <p><span className="text-zinc-500">Tema:</span> Dark Mode Nativo (Alto contraste operacional)</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader className="border-zinc-800">
              <CardTitle>Próxima Implementação (#55)</CardTitle>
              <CardDescription>Fila de pedidos, tempos de espera e alteração de status</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-zinc-400">
                A Issue #55 trará os cards de comandas da cozinha com os estados <code>pendente</code>, <code>em_preparo</code>, <code>pronto</code> e <code>entregue</code>.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
