import React, { useEffect, useState } from 'react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Select } from '../ui/Select'
import { financeiroService } from '../../services/financeiro'
import { CategoriaDespesa, Despesa } from '../../types/financeiro'
import { useAuth } from '../../contexts/AuthContext'

interface DespesaModalProps {
  isOpen: boolean
  onClose: () => void
  despesaEdicao?: Despesa | null
  onDespesaSalva: () => void
}

const OPCOES_CATEGORIA: { value: CategoriaDespesa; label: string }[] = [
  { value: 'insumos', label: 'Insumos & Ingredientes' },
  { value: 'contas_fixas', label: 'Contas Fixas (Aluguel, Luz, Água)' },
  { value: 'manutencao', label: 'Manutenção & Equipamentos' },
  { value: 'outros', label: 'Outras Despesas' },
]

export const DespesaModal: React.FC<DespesaModalProps> = ({
  isOpen,
  onClose,
  despesaEdicao,
  onDespesaSalva,
}) => {
  const { restauranteAtivo } = useAuth()
  const [descricao, setDescricao] = useState('')
  const [categoria, setCategoria] = useState<CategoriaDespesa>('insumos')
  const [valorStr, setValorStr] = useState('')
  const [dataPagamento, setDataPagamento] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      if (despesaEdicao) {
        setDescricao(despesaEdicao.descricao)
        setCategoria(despesaEdicao.categoria || 'outros')
        setValorStr(String(despesaEdicao.valor))
        setDataPagamento(despesaEdicao.data_pagamento)
      } else {
        setDescricao('')
        setCategoria('insumos')
        setValorStr('')
        setDataPagamento(new Date().toISOString().split('T')[0])
      }
      setErro(null)
    }
  }, [isOpen, despesaEdicao])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const descLimpa = descricao.trim()
    if (descLimpa.length < 2) {
      setErro('A descrição deve ter pelo menos 2 caracteres.')
      return
    }

    const valorNum = parseFloat(valorStr.replace(',', '.'))
    if (isNaN(valorNum) || valorNum <= 0) {
      setErro('O valor deve ser um número maior que zero.')
      return
    }

    if (!dataPagamento) {
      setErro('A data de pagamento é obrigatória.')
      return
    }

    try {
      setSalvando(true)
      setErro(null)

      if (despesaEdicao) {
        await financeiroService.atualizarDespesa(
          despesaEdicao.id,
          {
            descricao: descLimpa,
            categoria,
            valor: valorNum,
            data_pagamento: dataPagamento,
          },
          restauranteAtivo?.id
        )
      } else {
        await financeiroService.criarDespesa(
          {
            descricao: descLimpa,
            categoria,
            valor: valorNum,
            data_pagamento: dataPagamento,
          },
          restauranteAtivo?.id
        )
      }

      onDespesaSalva()
      onClose()
    } catch {
      setErro('Erro ao salvar a despesa. Verifique os dados informados.')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={despesaEdicao ? 'Editar Despesa' : 'Nova Despesa Operacional'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {erro && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {erro}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1">
            Descrição da Despesa
          </label>
          <Input
            type="text"
            placeholder="Ex: Compra de carnes no atacado, Conta de luz"
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1">
            Categoria
          </label>
          <Select
            value={categoria}
            onChange={(e) => setCategoria(e.target.value as CategoriaDespesa)}
            options={OPCOES_CATEGORIA}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1">
              Valor (R$)
            </label>
            <Input
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0,00"
              value={valorStr}
              onChange={(e) => setValorStr(e.target.value)}
              className="tabular-nums"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1">
              Data de Pagamento
            </label>
            <Input
              type="date"
              value={dataPagamento}
              onChange={(e) => setDataPagamento(e.target.value)}
              required
            />
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            type="button"
            variant="secondary"
            className="flex-1 min-h-[44px]"
            onClick={onClose}
            disabled={salvando}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            className="flex-1 min-h-[44px]"
            isLoading={salvando}
          >
            {despesaEdicao ? 'Salvar Alterações' : 'Cadastrar Despesa'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
