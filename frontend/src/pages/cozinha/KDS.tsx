import React, { useEffect, useState, useMemo } from 'react'
import {
  UtensilsCrossed,
  RefreshCw,
  Clock,
  Flame,
  CheckCircle2,
  LogOut,
} from 'lucide-react'
import { cozinhaService } from '../../services/cozinha'
import { CozinhaPedido, StatusItemCozinha } from '../../types/cozinha'
import { useAuth } from '../../contexts/AuthContext'
import { PedidoCard } from '../../components/cozinha/PedidoCard'
import { Button } from '../../components/ui/Button'

export const KDS: React.FC = () => {
  const { restauranteAtivo, logout, user } = useAuth()
  const [pedidos, setPedidos] = useState<CozinhaPedido[]>([])
  const [carregando, setCarregando] = useState(true)
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState<Date>(new Date())

  const carregarPedidos = async () => {
    try {
      setCarregando(true)
      const data = await cozinhaService.listarPedidos({
        restaurante_id: restauranteAtivo?.id,
      })
      setPedidos(data)
      setUltimaAtualizacao(new Date())
    } catch {
      // tratado com fallback
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarPedidos()
    const interval = setInterval(carregarPedidos, 10000)
    return () => clearInterval(interval)
  }, [restauranteAtivo?.id])

  const handleAtualizarStatus = async (pedidoId: string, novoStatus: StatusItemCozinha) => {
    try {
      await cozinhaService.atualizarStatusPedido(
        pedidoId,
        novoStatus,
        restauranteAtivo?.id
      )
      // Atualização otimista local
      setPedidos((atuais) =>
        atuais
          .map((p) => (p.id === pedidoId ? { ...p, status: novoStatus } : p))
          .filter((p) => novoStatus !== 'entregue' || p.id !== pedidoId)
      )
    } catch {
      alert('Não foi possível atualizar o status do pedido.')
      carregarPedidos()
    }
  }

  const pedidosPendentes = useMemo(
    () => pedidos.filter((p) => p.status === 'pendente'),
    [pedidos]
  )

  const pedidosEmPreparo = useMemo(
    () => pedidos.filter((p) => p.status === 'em_preparo'),
    [pedidos]
  )

  const pedidosProntos = useMemo(
    () => pedidos.filter((p) => p.status === 'pronto'),
    [pedidos]
  )

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col antialiased">
      {/* TopBar KDS Dark Permanente */}
      <header className="bg-zinc-900 border-b border-zinc-800 px-4 py-3 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <UtensilsCrossed size={20} strokeWidth={2} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-black text-lg text-white tracking-wide">Cozinha KDS</h1>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-zinc-800 text-amber-400 border border-amber-500/20">
                Ao Vivo
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              {restauranteAtivo?.nome || 'Hstronomia'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden sm:inline-block text-xs text-zinc-500 tabular-nums">
            Atualizado às {ultimaAtualizacao.toLocaleTimeString('pt-BR')}
          </span>

          <Button
            variant="secondary"
            size="sm"
            onClick={carregarPedidos}
            isLoading={carregando}
            className="border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 min-h-[40px]"
          >
            <RefreshCw size={16} strokeWidth={2} />
          </Button>

          {user && (
            <button
              type="button"
              onClick={logout}
              className="p-2 rounded-lg text-zinc-400 hover:text-red-400 hover:bg-zinc-800 transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center"
              title="Sair do terminal"
            >
              <LogOut size={18} strokeWidth={2} />
            </button>
          )}
        </div>
      </header>

      {/* Visão de 3 Colunas Kanban do KDS */}
      <main className="flex-1 p-4 overflow-x-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 min-w-[320px] max-w-7xl mx-auto h-full">
          {/* Coluna 1: Pendentes */}
          <section className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
              <div className="flex items-center gap-2">
                <Clock className="text-amber-400" size={18} strokeWidth={2} />
                <h2 className="font-bold text-sm uppercase tracking-wider text-zinc-200">
                  Aguardando
                </h2>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-zinc-800 text-xs font-bold text-amber-400 tabular-nums">
                {pedidosPendentes.length}
              </span>
            </div>

            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {pedidosPendentes.length === 0 ? (
                <div className="text-center py-12 text-zinc-600 text-xs font-medium">
                  Nenhum pedido pendente
                </div>
              ) : (
                pedidosPendentes.map((pedido) => (
                  <PedidoCard
                    key={pedido.id}
                    pedido={pedido}
                    onAtualizarStatus={handleAtualizarStatus}
                  />
                ))
              )}
            </div>
          </section>

          {/* Coluna 2: Em Preparo */}
          <section className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
              <div className="flex items-center gap-2">
                <Flame className="text-amber-500" size={18} strokeWidth={2} />
                <h2 className="font-bold text-sm uppercase tracking-wider text-zinc-200">
                  No Fogo / Montagem
                </h2>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-xs font-bold text-amber-400 tabular-nums border border-amber-500/30">
                {pedidosEmPreparo.length}
              </span>
            </div>

            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {pedidosEmPreparo.length === 0 ? (
                <div className="text-center py-12 text-zinc-600 text-xs font-medium">
                  Nenhum item em preparo no momento
                </div>
              ) : (
                pedidosEmPreparo.map((pedido) => (
                  <PedidoCard
                    key={pedido.id}
                    pedido={pedido}
                    onAtualizarStatus={handleAtualizarStatus}
                  />
                ))
              )}
            </div>
          </section>

          {/* Coluna 3: Prontos */}
          <section className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-4 flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800 mb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="text-emerald-400" size={18} strokeWidth={2} />
                <h2 className="font-bold text-sm uppercase tracking-wider text-zinc-200">
                  Prontos p/ Servir
                </h2>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-xs font-bold text-emerald-400 tabular-nums border border-emerald-500/30">
                {pedidosProntos.length}
              </span>
            </div>

            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {pedidosProntos.length === 0 ? (
                <div className="text-center py-12 text-zinc-600 text-xs font-medium">
                  Nenhum prato aguardando entrega
                </div>
              ) : (
                pedidosProntos.map((pedido) => (
                  <PedidoCard
                    key={pedido.id}
                    pedido={pedido}
                    onAtualizarStatus={handleAtualizarStatus}
                  />
                ))
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
