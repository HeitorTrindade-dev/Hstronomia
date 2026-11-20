import React, { useEffect, useState, useCallback } from 'react'
import { QrCode, Banknote, CreditCard, Receipt, LucideIcon } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { comandaService } from '../../services/comanda'
import { ComandaPrevia, MetodoPagamento } from '../../types/comanda'
import { useAuth } from '../../contexts/AuthContext'

interface FecharComandaModalProps {
  isOpen: boolean
  onClose: () => void
  comandaId: string
  identificadorTitulo?: string
  onComandaFechada: () => void
}

const METODOS_PAGAMENTO: {
  id: MetodoPagamento
  label: string
  icone: LucideIcon
}[] = [
  { id: 'pix', label: 'Pix', icone: QrCode },
  { id: 'dinheiro', label: 'Dinheiro', icone: Banknote },
  { id: 'cartao_credito', label: 'Crédito', icone: CreditCard },
  { id: 'cartao_debito', label: 'Débito', icone: CreditCard },
]

export const FecharComandaModal: React.FC<FecharComandaModalProps> = ({
  isOpen,
  onClose,
  comandaId,
  identificadorTitulo,
  onComandaFechada,
}) => {
  const { restauranteAtivo } = useAuth()
  const [previa, setPrevia] = useState<ComandaPrevia | null>(null)
  const [incluirTaxa, setIncluirTaxa] = useState(true)
  const [descontoStr, setDescontoStr] = useState('0')
  const [metodoPagamento, setMetodoPagamento] = useState<MetodoPagamento>('pix')
  const [valorRecebidoStr, setValorRecebidoStr] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [fechando, setFechando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const carregarPrevia = useCallback(async (taxa: boolean, descVal: number) => {
    try {
      setCarregando(true)
      const data = await comandaService.obterPrevia(comandaId, {
        incluir_taxa_servico: taxa,
        desconto: descVal,
        restaurante_id: restauranteAtivo?.id,
      })
      setPrevia(data)
    } catch {
      setErro('Não foi possível obter a prévia da comanda.')
    } finally {
      setCarregando(false)
    }
  }, [comandaId, restauranteAtivo?.id])

  useEffect(() => {
    if (isOpen) {
      setIncluirTaxa(true)
      setDescontoStr('0')
      setMetodoPagamento('pix')
      setValorRecebidoStr('')
      setErro(null)
      carregarPrevia(true, 0)
    }
  }, [isOpen, carregarPrevia])

  const handleToggleTaxa = () => {
    const novoValor = !incluirTaxa
    setIncluirTaxa(novoValor)
    const desc = parseFloat(descontoStr.replace(',', '.')) || 0
    carregarPrevia(novoValor, desc)
  }

  const handleDescontoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valStr = e.target.value
    setDescontoStr(valStr)
    const desc = parseFloat(valStr.replace(',', '.')) || 0
    if (desc >= 0) {
      carregarPrevia(incluirTaxa, desc)
    }
  }

  const formatarMoeda = (valor: number | string | undefined) => {
    if (valor === undefined || valor === null) return 'R$ 0,00'
    const num = typeof valor === 'string' ? parseFloat(valor) : valor
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  const valorTotalNum = previa ? Number(previa.valor_total) : 0
  const valorRecebidoNum = parseFloat(valorRecebidoStr.replace(',', '.')) || 0
  const troco = Math.max(0, valorRecebidoNum - valorTotalNum)

  const handleFechar = async () => {
    if (!previa) return
    const desc = parseFloat(descontoStr.replace(',', '.')) || 0

    if (metodoPagamento === 'dinheiro' && valorRecebidoNum > 0 && valorRecebidoNum < valorTotalNum) {
      setErro('O valor recebido em dinheiro é inferior ao total da comanda.')
      return
    }

    try {
      setFechando(true)
      setErro(null)
      await comandaService.fecharComanda(
        comandaId,
        {
          metodo_pagamento: metodoPagamento,
          incluir_taxa_servico: incluirTaxa,
          desconto: desc,
        },
        restauranteAtivo?.id
      )
      onComandaFechada()
      onClose()
    } catch {
      setErro('Erro ao fechar a comanda. Verifique se há pedidos pendentes.')
    } finally {
      setFechando(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Fechar Conta — ${identificadorTitulo || 'Comanda'}`}
    >
      <div className="space-y-4">
        {erro && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {erro}
          </div>
        )}

        {/* Resumo Financeiro da Prévia */}
        <div className="bg-zinc-50 border border-zinc-200 rounded-xl p-4 space-y-2.5">
          <div className="flex justify-between items-center text-sm text-zinc-600">
            <span>Subtotal dos itens:</span>
            <span className="font-semibold text-zinc-900 tabular-nums">
              {formatarMoeda(previa?.subtotal)}
            </span>
          </div>

          {/* Toggle Taxa de Serviço 10% */}
          <div className="flex justify-between items-center py-1 border-t border-zinc-200 text-sm">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={incluirTaxa}
                onChange={handleToggleTaxa}
                className="w-4 h-4 rounded text-zinc-900 focus:ring-zinc-900 border-zinc-300"
              />
              <span className="text-zinc-700">Taxa de serviço (10%)</span>
            </label>
            <span className="font-semibold text-zinc-900 tabular-nums">
              {incluirTaxa ? formatarMoeda(previa?.taxa_servico) : 'R$ 0,00'}
            </span>
          </div>

          {/* Campo de Desconto */}
          <div className="flex justify-between items-center py-1 border-t border-zinc-200 text-sm">
            <span className="text-zinc-700">Desconto em R$:</span>
            <div className="w-28">
              <Input
                type="number"
                step="0.50"
                min="0"
                value={descontoStr}
                onChange={handleDescontoChange}
                className="text-right h-8 text-xs font-semibold tabular-nums"
              />
            </div>
          </div>

          {/* Total Geral Destacado */}
          <div className="flex justify-between items-center pt-2 border-t-2 border-zinc-300">
            <span className="text-base font-bold text-zinc-900">Total a Pagar:</span>
            <span className="text-2xl font-black text-emerald-600 tabular-nums">
              {formatarMoeda(previa?.valor_total)}
            </span>
          </div>
        </div>

        {/* Seleção do Método de Pagamento */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
            Método de Pagamento
          </label>
          <div className="grid grid-cols-2 gap-2">
            {METODOS_PAGAMENTO.map((metodo) => {
              const Icone = metodo.icone
              const selecionado = metodoPagamento === metodo.id
              return (
                <button
                  key={metodo.id}
                  type="button"
                  onClick={() => setMetodoPagamento(metodo.id)}
                  className={`p-3 rounded-xl border flex items-center gap-2.5 transition-all min-h-[48px] ${
                    selecionado
                      ? 'border-zinc-900 bg-zinc-900 text-white shadow-sm'
                      : 'border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50'
                  }`}
                >
                  <Icone size={18} strokeWidth={2} />
                  <span className="text-sm font-semibold">{metodo.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Seletor Dinheiro com Troco */}
        {metodoPagamento === 'dinheiro' && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 space-y-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-amber-900">
              Valor em Dinheiro Entregue pelo Cliente
            </label>
            <Input
              type="number"
              step="1.00"
              min="0"
              placeholder="Ex: 50,00"
              value={valorRecebidoStr}
              onChange={(e) => setValorRecebidoStr(e.target.value)}
              className="bg-white border-amber-300 tabular-nums"
            />
            {valorRecebidoNum > 0 && (
              <div className="flex justify-between items-center pt-1 text-sm">
                <span className="font-semibold text-amber-950">Troco a devolver:</span>
                <span className="font-bold text-base text-amber-900 tabular-nums">
                  {formatarMoeda(troco)}
                </span>
              </div>
            )}
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <Button
            variant="secondary"
            className="flex-1 min-h-[48px]"
            onClick={onClose}
            disabled={fechando}
          >
            Voltar
          </Button>
          <Button
            variant="primary"
            className="flex-1 min-h-[48px] bg-emerald-600 hover:bg-emerald-700 border-emerald-600"
            isLoading={fechando || carregando}
            onClick={handleFechar}
          >
            <Receipt size={18} className="mr-2" strokeWidth={2} />
            Confirmar Fechamento
          </Button>
        </div>
      </div>
    </Modal>
  )
}
