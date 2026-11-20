import React, { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Users, ShoppingBag, Clock, RefreshCw } from 'lucide-react'
import { comandaService } from '../../services/comanda'
import { Comanda, ComandaCreateInput } from '../../types/comanda'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/ui/Button'
import { AbrirComandaModal } from '../../components/garcom/AbrirComandaModal'
import { TopBar } from '../../components/layout/TopBar'

const TOTAL_MESAS_PADRAO = 20

export const Mesas: React.FC = () => {
  const navigate = useNavigate()
  const { restauranteAtivo } = useAuth()
  const [comandasAbertas, setComandasAbertas] = useState<Comanda[]>([])
  const [carregando, setCarregando] = useState(true)
  const [modalAbrirAberto, setModalAbrirAberto] = useState(false)
  const [mesaPreSelecionada, setMesaPreSelecionada] = useState<number | undefined>(undefined)
  const [abaAtiva, setAbaAtiva] = useState<'mesas' | 'balcao'>('mesas')

  const carregarComandas = async () => {
    try {
      setCarregando(true)
      const data = await comandaService.listarComandas({
        status: 'aberta',
        restaurante_id: restauranteAtivo?.id,
      })
      setComandasAbertas(data)
    } catch {
      // Falha tratada silenciosamente com estado
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarComandas()
    // Polling suave a cada 20 segundos para manter salão sincronizado
    const interval = setInterval(carregarComandas, 20000)
    return () => clearInterval(interval)
  }, [restauranteAtivo?.id])

  // Mapeamento de mesas ocupadas por número de mesa
  const mapaMesasOcupadas = useMemo(() => {
    const mapa = new Map<number, Comanda>()
    comandasAbertas.forEach((cmd) => {
      if (cmd.tipo_atendimento === 'mesa' && cmd.numero_mesa) {
        mapa.set(cmd.numero_mesa, cmd)
      }
    })
    return mapa
  }, [comandasAbertas])

  const comandasBalcaoViagem = useMemo(() => {
    return comandasAbertas.filter((cmd) => cmd.tipo_atendimento !== 'mesa')
  }, [comandasAbertas])

  const handleMesaClick = (numeroMesa: number) => {
    const comanda = mapaMesasOcupadas.get(numeroMesa)
    if (comanda) {
      navigate(`/garcom/comandas/${comanda.id}`)
    } else {
      setMesaPreSelecionada(numeroMesa)
      setModalAbrirAberto(true)
    }
  }

  const formatarMoeda = (valor: number | string) => {
    const num = typeof valor === 'string' ? parseFloat(valor) : valor
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  const calcularMinutosAberto = (criadoEm: string) => {
    const inicio = new Date(criadoEm).getTime()
    const agora = Date.now()
    const minutos = Math.floor((agora - inicio) / 60000)
    if (minutos < 1) return 'Agora'
    if (minutos < 60) return `${minutos} min`
    const horas = Math.floor(minutos / 60)
    const resto = minutos % 60
    return `${horas}h ${resto}m`
  }

  const handleAbrirComanda = async (data: ComandaCreateInput) => {
    const nova = await comandaService.abrirComanda(data, restauranteAtivo?.id)
    navigate(`/garcom/comandas/${nova.id}`)
  }

  // Lista de mesas 1..20 mais qualquer mesa além de 20 que esteja ocupada
  const mesasNumeros = useMemo(() => {
    const lista = Array.from({ length: TOTAL_MESAS_PADRAO }, (_, i) => i + 1)
    mapaMesasOcupadas.forEach((_, mesaNum) => {
      if (!lista.includes(mesaNum)) {
        lista.push(mesaNum)
      }
    })
    return lista.sort((a, b) => a - b)
  }, [mapaMesasOcupadas])

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      <TopBar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-4 space-y-4">
        {/* Cabeçalho da Visão de Salão */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-zinc-900">Salão & Atendimento</h1>
            <p className="text-xs sm:text-sm text-zinc-500">
              Controle rápido de comandas, mesas e pedidos
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={carregarComandas}
              isLoading={carregando}
              className="min-h-[44px]"
            >
              <RefreshCw size={16} strokeWidth={2} />
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setMesaPreSelecionada(undefined)
                setModalAbrirAberto(true)
              }}
              className="min-h-[44px] flex-1 sm:flex-none"
            >
              <Plus size={18} className="mr-1" strokeWidth={2} />
              Nova Comanda
            </Button>
          </div>
        </div>

        {/* Abas Mesas vs Balcão */}
        <div className="flex border-b border-zinc-200 gap-4">
          <button
            type="button"
            onClick={() => setAbaAtiva('mesas')}
            className={`pb-2.5 text-sm font-semibold transition-colors flex items-center gap-2 min-h-[44px] border-b-2 ${
              abaAtiva === 'mesas'
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            <Users size={16} strokeWidth={2} />
            Mesas ({mapaMesasOcupadas.size} ocupadas)
          </button>
          <button
            type="button"
            onClick={() => setAbaAtiva('balcao')}
            className={`pb-2.5 text-sm font-semibold transition-colors flex items-center gap-2 min-h-[44px] border-b-2 ${
              abaAtiva === 'balcao'
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-700'
            }`}
          >
            <ShoppingBag size={16} strokeWidth={2} />
            Balcão & Viagem ({comandasBalcaoViagem.length})
          </button>
        </div>

        {/* Conteúdo da Aba Mesas */}
        {abaAtiva === 'mesas' && (
          <div className="space-y-4">
            {/* Legenda do Semáforo */}
            <div className="flex items-center gap-4 text-xs font-medium text-zinc-600 bg-white p-2.5 rounded-xl border border-zinc-200">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
                Livre (Toque para abrir)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
                Ocupada (Toque para detalhes)
              </span>
            </div>

            {/* Grid de Mesas */}
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-3">
              {mesasNumeros.map((num) => {
                const comanda = mapaMesasOcupadas.get(num)
                const ocupada = Boolean(comanda)

                return (
                  <button
                    key={num}
                    type="button"
                    onClick={() => handleMesaClick(num)}
                    className={`p-4 rounded-2xl border text-left flex flex-col justify-between transition-all min-h-[110px] active:scale-[0.98] ${
                      ocupada
                        ? 'border-amber-400 bg-amber-50/80 shadow-sm hover:border-amber-500'
                        : 'border-zinc-200 bg-white hover:border-emerald-500 hover:bg-emerald-50/30'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="text-xl font-black text-zinc-900 tabular-nums">
                        Mesa {num}
                      </span>
                      <span
                        className={`w-3.5 h-3.5 rounded-full ${
                          ocupada ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'
                        }`}
                      />
                    </div>

                    {ocupada && comanda ? (
                      <div className="space-y-1 mt-2">
                        <div className="flex items-center justify-between text-xs text-amber-900">
                          <span className="flex items-center gap-1 font-medium">
                            <Clock size={12} strokeWidth={2} />
                            {calcularMinutosAberto(comanda.criado_em)}
                          </span>
                          <span className="font-bold tabular-nums">
                            {formatarMoeda(comanda.valor_total || 0)}
                          </span>
                        </div>
                        {comanda.identificador && (
                          <p className="text-[11px] text-zinc-500 truncate">
                            {comanda.identificador}
                          </p>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs font-semibold text-emerald-700 mt-3">
                        Livre
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Conteúdo da Aba Balcão e Viagem */}
        {abaAtiva === 'balcao' && (
          <div className="space-y-3">
            {comandasBalcaoViagem.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-2xl border border-zinc-200">
                <ShoppingBag className="mx-auto text-zinc-300 mb-2" size={36} strokeWidth={1.5} />
                <p className="text-sm font-semibold text-zinc-700">Nenhum pedido de balcão ativo</p>
                <p className="text-xs text-zinc-400 mt-1">
                  Abra uma nova comanda selecionando o tipo Balcão ou Viagem.
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setMesaPreSelecionada(undefined)
                    setModalAbrirAberto(true)
                  }}
                  className="mt-4"
                >
                  <Plus size={16} className="mr-1" strokeWidth={2} />
                  Abrir Comanda de Balcão
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {comandasBalcaoViagem.map((cmd) => (
                  <button
                    key={cmd.id}
                    type="button"
                    onClick={() => navigate(`/garcom/comandas/${cmd.id}`)}
                    className="p-4 rounded-2xl border border-zinc-200 bg-white hover:border-zinc-400 text-left transition-all shadow-sm active:scale-[0.99] flex flex-col justify-between min-h-[100px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700">
                        {cmd.tipo_atendimento === 'viagem' ? 'Para Viagem' : 'Balcão'}
                      </span>
                      <span className="text-xs font-semibold text-zinc-500 tabular-nums flex items-center gap-1">
                        <Clock size={12} strokeWidth={2} />
                        {calcularMinutosAberto(cmd.criado_em)}
                      </span>
                    </div>

                    <div className="mt-3">
                      <p className="font-bold text-zinc-900 text-base">
                        {cmd.identificador || 'Cliente sem nome'}
                      </p>
                      <div className="flex items-center justify-between mt-1 text-sm">
                        <span className="text-xs text-zinc-500">Total:</span>
                        <span className="font-bold text-zinc-900 tabular-nums">
                          {formatarMoeda(cmd.valor_total || 0)}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <AbrirComandaModal
        isOpen={modalAbrirAberto}
        onClose={() => setModalAbrirAberto(false)}
        mesaPreSelecionada={mesaPreSelecionada}
        onSave={handleAbrirComanda}
      />
    </div>
  )
}
