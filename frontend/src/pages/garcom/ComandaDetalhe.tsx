import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Plus,
  Receipt,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
} from 'lucide-react'
import { comandaService } from '../../services/comanda'
import { cozinhaService } from '../../services/cozinha'
import { Comanda, ItemComanda } from '../../types/comanda'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { TopBar } from '../../components/layout/TopBar'
import { AdicionarItemModal } from '../../components/garcom/AdicionarItemModal'
import { FecharComandaModal } from '../../components/garcom/FecharComandaModal'
import { CancelarComandaModal } from '../../components/garcom/CancelarComandaModal'

export const ComandaDetalhe: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { restauranteAtivo } = useAuth()

  const [comanda, setComanda] = useState<Comanda | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const [modalAdicionarAberto, setModalAdicionarAberto] = useState(false)
  const [modalFecharAberto, setModalFecharAberto] = useState(false)
  const [modalCancelarAberto, setModalCancelarAberto] = useState(false)
  const [removendoItemId, setRemovendoItemId] = useState<string | null>(null)
  const [marcandoEntregueId, setMarcandoEntregueId] = useState<string | null>(null)

  const carregarComanda = useCallback(async () => {
    if (!id) return
    try {
      setCarregando(true)
      setErro(null)
      const data = await comandaService.obterComanda(id, restauranteAtivo?.id)
      setComanda(data)
    } catch {
      setErro('Não foi possível carregar a comanda.')
    } finally {
      setCarregando(false)
    }
  }, [id, restauranteAtivo?.id])

  useEffect(() => {
    carregarComanda()
    const interval = setInterval(carregarComanda, 15000)
    return () => clearInterval(interval)
  }, [carregarComanda])

  const handleRemoverItem = async (itemId: string) => {
    if (!id) return
    if (!confirm('Deseja remover este item pendente da comanda?')) return

    try {
      setRemovendoItemId(itemId)
      await comandaService.removerItem(id, itemId, restauranteAtivo?.id)
      await carregarComanda()
    } catch {
      alert('Não foi possível remover o item. Verifique se ele já entrou em preparo.')
    } finally {
      setRemovendoItemId(null)
    }
  }

  const handleMarcarEntregue = async (itemId: string) => {
    try {
      setMarcandoEntregueId(itemId)
      await cozinhaService.atualizarStatusPedido(
        itemId,
        'entregue',
        restauranteAtivo?.id
      )
      await carregarComanda()
    } catch {
      alert('Erro ao marcar item como entregue.')
    } finally {
      setMarcandoEntregueId(null)
    }
  }

  const formatarMoeda = (valor: number | string | undefined) => {
    if (valor === undefined || valor === null) return 'R$ 0,00'
    const num = typeof valor === 'string' ? parseFloat(valor) : valor
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  const renderBadgeStatusItem = (item: ItemComanda) => {
    switch (item.status) {
      case 'pendente':
        return <Badge variant="zinc">Pendente</Badge>
      case 'em_preparo':
        return <Badge variant="amber">Em preparo</Badge>
      case 'pronto':
        return <Badge variant="emerald">Pronto p/ servir</Badge>
      case 'entregue':
        return <Badge variant="sky">Entregue</Badge>
      case 'cancelado':
        return <Badge variant="red">Cancelado</Badge>
      default:
        return <Badge variant="zinc">{item.status}</Badge>
    }
  }

  const tituloComanda = comanda?.tipo_atendimento === 'mesa'
    ? `Mesa ${comanda.numero_mesa}`
    : comanda?.tipo_atendimento === 'viagem'
    ? 'Para Viagem'
    : 'Balcão'

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col pb-28">
      <TopBar />

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-4 space-y-4">
        {/* Barra superior de navegação */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate('/garcom/mesas')}
            className="flex items-center gap-2 text-sm font-semibold text-zinc-600 hover:text-zinc-900 transition-colors min-h-[44px]"
          >
            <ArrowLeft size={18} strokeWidth={2} />
            Voltar ao Salão
          </button>

          <Button
            variant="secondary"
            size="sm"
            onClick={carregarComanda}
            isLoading={carregando}
            className="min-h-[44px]"
          >
            <RefreshCw size={16} strokeWidth={2} />
          </Button>
        </div>

        {erro && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 flex items-center gap-2">
            <AlertCircle size={18} />
            {erro}
          </div>
        )}

        {comanda && (
          <>
            {/* Card de Identificação da Comanda */}
            <div className="bg-white border border-zinc-200 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-black text-zinc-900">{tituloComanda}</h1>
                  {comanda.identificador && (
                    <p className="text-sm font-medium text-zinc-600">{comanda.identificador}</p>
                  )}
                </div>
                <Badge
                  variant={
                    comanda.status === 'aberta'
                      ? 'amber'
                      : comanda.status === 'fechada'
                      ? 'emerald'
                      : 'red'
                  }
                >
                  {comanda.status === 'aberta'
                    ? 'Comanda Aberta'
                    : comanda.status === 'fechada'
                    ? 'Fechada'
                    : 'Cancelada'}
                </Badge>
              </div>

              <div className="flex items-center justify-between text-xs text-zinc-500 pt-2 border-t border-zinc-100">
                <span className="flex items-center gap-1.5 font-medium">
                  <Clock size={14} strokeWidth={2} />
                  Aberta em {new Date(comanda.criado_em).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-base font-bold text-zinc-900 tabular-nums">
                  Subtotal: {formatarMoeda(comanda.subtotal)}
                </span>
              </div>
            </div>

            {/* Lista de Itens do Pedido */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-500">
                  Itens do Pedido ({comanda.itens?.length || 0})
                </h2>
              </div>

              {(!comanda.itens || comanda.itens.length === 0) ? (
                <div className="text-center py-10 bg-white rounded-2xl border border-zinc-200">
                  <p className="text-sm font-medium text-zinc-600">Nenhum item lançado ainda</p>
                  <p className="text-xs text-zinc-400 mt-1">
                    Toque no botão abaixo para adicionar pedidos da cozinha ou bar.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {comanda.itens.map((item) => (
                    <div
                      key={item.id}
                      className="bg-white border border-zinc-200 rounded-xl p-4 shadow-sm space-y-2"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-baseline gap-2">
                            <span className="font-bold text-zinc-900 text-sm tabular-nums">
                              {item.quantidade}x
                            </span>
                            <span className="font-semibold text-zinc-900 text-sm">
                              {item.nome_item}
                            </span>
                          </div>

                          {item.observacao && (
                            <p className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md inline-block mt-1">
                              Obs: {item.observacao}
                            </p>
                          )}
                        </div>

                        <div className="text-right shrink-0">
                          <p className="font-bold text-zinc-900 tabular-nums text-sm">
                            {formatarMoeda(Number(item.preco_unitario) * item.quantidade)}
                          </p>
                          <p className="text-[11px] text-zinc-400 tabular-nums">
                            {formatarMoeda(item.preco_unitario)} un.
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-zinc-100">
                        <div>{renderBadgeStatusItem(item)}</div>

                        <div className="flex items-center gap-2">
                          {/* Botão para garçom entregar se estiver pronto */}
                          {item.status === 'pronto' && (
                            <Button
                              variant="primary"
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 h-8 text-xs min-h-[36px]"
                              isLoading={marcandoEntregueId === item.id}
                              onClick={() => handleMarcarEntregue(item.id)}
                            >
                              <CheckCircle2 size={14} className="mr-1" strokeWidth={2} />
                              Servido / Entregue
                            </Button>
                          )}

                          {/* Botão de exclusão somente para pendentes */}
                          {item.status === 'pendente' && comanda.status === 'aberta' && (
                            <button
                              type="button"
                              onClick={() => handleRemoverItem(item.id)}
                              disabled={removendoItemId === item.id}
                              className="text-zinc-400 hover:text-red-600 p-2 rounded-lg transition-colors min-h-[36px] min-w-[36px] flex items-center justify-center"
                              title="Remover item pendente"
                            >
                              <Trash2 size={16} strokeWidth={2} />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Barra Inferior Fixa de Ações Touch-Friendly (>=44px) */}
      {comanda && comanda.status === 'aberta' && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t border-zinc-200 p-3 shadow-lg z-20">
          <div className="max-w-3xl mx-auto flex items-center gap-2">
            <Button
              variant="secondary"
              className="text-red-600 hover:bg-red-50 hover:border-red-200 min-h-[50px] px-3 shrink-0"
              onClick={() => setModalCancelarAberto(true)}
              title="Cancelar comanda"
            >
              <Trash2 size={18} strokeWidth={2} />
            </Button>

            <Button
              variant="primary"
              className="flex-1 min-h-[50px] text-sm font-bold shadow-md"
              onClick={() => setModalAdicionarAberto(true)}
            >
              <Plus size={18} className="mr-1.5" strokeWidth={2} />
              Lançar Itens
            </Button>

            <Button
              variant="primary"
              className="flex-1 min-h-[50px] text-sm font-bold bg-emerald-600 hover:bg-emerald-700 border-emerald-600 shadow-md"
              onClick={() => setModalFecharAberto(true)}
            >
              <Receipt size={18} className="mr-1.5" strokeWidth={2} />
              Fechar Conta
            </Button>
          </div>
        </div>
      )}

      {/* Modais de Ação */}
      {id && (
        <>
          <AdicionarItemModal
            isOpen={modalAdicionarAberto}
            onClose={() => setModalAdicionarAberto(false)}
            comandaId={id}
            onItemAdicionado={carregarComanda}
          />

          <FecharComandaModal
            isOpen={modalFecharAberto}
            onClose={() => setModalFecharAberto(false)}
            comandaId={id}
            identificadorTitulo={tituloComanda}
            onComandaFechada={() => {
              carregarComanda()
              navigate('/garcom/mesas')
            }}
          />

          <CancelarComandaModal
            isOpen={modalCancelarAberto}
            onClose={() => setModalCancelarAberto(false)}
            comandaId={id}
            identificadorTitulo={tituloComanda}
            onComandaCancelada={() => {
              navigate('/garcom/mesas')
            }}
          />
        </>
      )}
    </div>
  )
}
