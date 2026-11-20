import React, { useEffect, useState, useMemo } from 'react'
import { Search, Plus, Minus, Check } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { cardapioService } from '../../services/cardapio'
import { comandaService } from '../../services/comanda'
import { Item } from '../../types/cardapio'
import { useAuth } from '../../contexts/AuthContext'

interface AdicionarItemModalProps {
  isOpen: boolean
  onClose: () => void
  comandaId: string
  onItemAdicionado: () => void
}

const CHIPS_OBSERVACOES = [
  'Sem cebola',
  'Ao ponto',
  'Sem gelo',
  'Gelo e limão',
  'Bem passado',
  'Mal passado',
  'Sem açúcar',
  'Molho à parte',
]

export const AdicionarItemModal: React.FC<AdicionarItemModalProps> = ({
  isOpen,
  onClose,
  comandaId,
  onItemAdicionado,
}) => {
  const { restauranteAtivo } = useAuth()
  const [itens, setItens] = useState<Item[]>([])
  const [busca, setBusca] = useState('')
  const [itemSelecionado, setItemSelecionado] = useState<Item | null>(null)
  const [quantidade, setQuantidade] = useState<number>(1)
  const [observacaoLivre, setObservacaoLivre] = useState('')
  const [chipsSelecionados, setChipsSelecionados] = useState<string[]>([])
  const [carregando, setCarregando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setItemSelecionado(null)
      setQuantidade(1)
      setObservacaoLivre('')
      setChipsSelecionados([])
      setBusca('')
      setErro(null)
      carregarItensCardapio()
    }
  }, [isOpen])

  const carregarItensCardapio = async () => {
    if (!restauranteAtivo?.id) return
    try {
      setCarregando(true)
      const data = await cardapioService.listarItens({
        apenas_disponiveis: true,
        restaurante_id: restauranteAtivo.id,
      })
      setItens(data)
    } catch {
      setErro('Não foi possível carregar os itens do cardápio.')
    } finally {
      setCarregando(false)
    }
  }

  const itensFiltrados = useMemo(() => {
    return itens.filter((i) => {
      const termo = busca.toLowerCase()
      const bateNome = i.nome.toLowerCase().includes(termo)
      const bateDesc = i.descricao ? i.descricao.toLowerCase().includes(termo) : false
      return bateNome || bateDesc
    })
  }, [itens, busca])

  const toggleChip = (chip: string) => {
    if (chipsSelecionados.includes(chip)) {
      setChipsSelecionados(chipsSelecionados.filter((c) => c !== chip))
    } else {
      setChipsSelecionados([...chipsSelecionados, chip])
    }
  }

  const handleConfirmar = async () => {
    if (!itemSelecionado) return

    const obsArray = [...chipsSelecionados]
    if (observacaoLivre.trim()) {
      obsArray.push(observacaoLivre.trim())
    }
    const observacaoFinal = obsArray.length > 0 ? obsArray.join('; ') : null

    try {
      setSalvando(true)
      setErro(null)
      await comandaService.adicionarItem(
        comandaId,
        {
          item_id: itemSelecionado.id,
          quantidade,
          observacao: observacaoFinal,
        },
        restauranteAtivo?.id
      )
      onItemAdicionado()
      onClose()
    } catch {
      setErro('Erro ao adicionar o item à comanda. Tente novamente.')
    } finally {
      setSalvando(false)
    }
  }

  const formatarPreco = (valor: number | string) => {
    const num = typeof valor === 'string' ? parseFloat(valor) : valor
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={itemSelecionado ? `Adicionar: ${itemSelecionado.nome}` : 'Adicionar Item ao Pedido'}
    >
      <div className="space-y-4">
        {erro && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {erro}
          </div>
        )}

        {!itemSelecionado ? (
          <>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400"
                size={18}
                strokeWidth={2}
              />
              <Input
                type="text"
                placeholder="Buscar prato, bebida ou sobremesa..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
              {carregando ? (
                <div className="py-8 text-center text-sm text-zinc-500">
                  Carregando cardápio...
                </div>
              ) : itensFiltrados.length === 0 ? (
                <div className="py-8 text-center text-sm text-zinc-500">
                  Nenhum item encontrado.
                </div>
              ) : (
                itensFiltrados.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setItemSelecionado(item)
                      setQuantidade(1)
                    }}
                    className="w-full text-left p-3.5 rounded-xl border border-zinc-200 hover:border-zinc-400 hover:bg-zinc-50 transition-all flex items-center justify-between min-h-[56px]"
                  >
                    <div className="pr-2">
                      <p className="font-semibold text-zinc-900 text-sm">{item.nome}</p>
                      {item.descricao && (
                        <p className="text-xs text-zinc-500 line-clamp-1">{item.descricao}</p>
                      )}
                    </div>
                    <span className="font-semibold text-zinc-900 tabular-nums text-sm whitespace-nowrap">
                      {formatarPreco(item.preco)}
                    </span>
                  </button>
                ))
              )}
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-zinc-50 rounded-xl border border-zinc-200">
              <div>
                <p className="font-bold text-zinc-900">{itemSelecionado.nome}</p>
                <p className="text-xs text-zinc-500 tabular-nums">
                  Preço unitário: {formatarPreco(itemSelecionado.preco)}
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setItemSelecionado(null)}
              >
                Trocar item
              </Button>
            </div>

            {/* Seletor de Quantidade Touch-Friendly */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
                Quantidade
              </label>
              <div className="flex items-center justify-center gap-4 bg-zinc-50 p-2 rounded-xl border border-zinc-200">
                <button
                  type="button"
                  disabled={quantidade <= 1}
                  onClick={() => setQuantidade((q) => Math.max(1, q - 1))}
                  className="w-12 h-12 flex items-center justify-center rounded-lg bg-white border border-zinc-300 text-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed active:bg-zinc-100 transition-colors"
                >
                  <Minus size={20} strokeWidth={2} />
                </button>
                <span className="text-2xl font-bold tabular-nums text-zinc-900 min-w-[3rem] text-center">
                  {quantidade}
                </span>
                <button
                  type="button"
                  onClick={() => setQuantidade((q) => q + 1)}
                  className="w-12 h-12 flex items-center justify-center rounded-lg bg-white border border-zinc-300 text-zinc-800 active:bg-zinc-100 transition-colors"
                >
                  <Plus size={20} strokeWidth={2} />
                </button>
              </div>
            </div>

            {/* Chips Rápidos de Observação */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
                Observações Rápidas
              </label>
              <div className="flex flex-wrap gap-2">
                {CHIPS_OBSERVACOES.map((chip) => {
                  const ativo = chipsSelecionados.includes(chip)
                  return (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => toggleChip(chip)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors flex items-center gap-1.5 min-h-[36px] ${
                        ativo
                          ? 'bg-zinc-900 text-white'
                          : 'bg-zinc-100 text-zinc-700 hover:bg-zinc-200'
                      }`}
                    >
                      {ativo && <Check size={14} strokeWidth={2} />}
                      {chip}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Campo Livre de Observação */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1">
                Outra Observação
              </label>
              <Input
                type="text"
                placeholder="Ex: sem pimenta, dividir em 2 pratos..."
                value={observacaoLivre}
                onChange={(e) => setObservacaoLivre(e.target.value)}
              />
            </div>

            {/* Total parcial do item */}
            <div className="p-3 bg-zinc-100 rounded-xl flex items-center justify-between">
              <span className="text-sm font-medium text-zinc-700">Subtotal do item:</span>
              <span className="text-base font-bold text-zinc-900 tabular-nums">
                {formatarPreco(Number(itemSelecionado.preco) * quantidade)}
              </span>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                variant="secondary"
                className="flex-1 min-h-[48px]"
                onClick={() => setItemSelecionado(null)}
              >
                Voltar
              </Button>
              <Button
                variant="primary"
                className="flex-1 min-h-[48px]"
                isLoading={salvando}
                onClick={handleConfirmar}
              >
                Adicionar ({quantidade})
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
