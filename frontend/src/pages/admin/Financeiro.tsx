import React, { useEffect, useState, useCallback, useMemo } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Plus,
  Calendar,
  Pencil,
  Trash2,
  RefreshCw,
} from 'lucide-react'
import { TopBar } from '../../components/layout/TopBar'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { KpiCard } from '../../components/financeiro/KpiCard'
import { DespesaModal } from '../../components/financeiro/DespesaModal'
import { financeiroService } from '../../services/financeiro'
import { Despesa, ResumoFinanceiro } from '../../types/financeiro'
import { useAuth } from '../../contexts/AuthContext'

type PeriodoTipo = 'hoje' | '7dias' | 'mes'

export const Financeiro: React.FC = () => {
  const { restauranteAtivo } = useAuth()
  const [periodo, setPeriodo] = useState<PeriodoTipo>('mes')
  const [resumo, setResumo] = useState<ResumoFinanceiro | null>(null)
  const [despesas, setDespesas] = useState<Despesa[]>([])
  const [carregando, setCarregando] = useState(true)
  const [modalDespesaAberto, setModalDespesaAberto] = useState(false)
  const [despesaEdicao, setDespesaEdicao] = useState<Despesa | null>(null)
  const [excluindoId, setExcluindoId] = useState<string | null>(null)

  const calcularDatasPeriodo = useCallback((tipo: PeriodoTipo) => {
    const hoje = new Date()
    const hojeStr = hoje.toISOString().split('T')[0]

    if (tipo === 'hoje') {
      return { inicio: hojeStr, fim: hojeStr }
    }
    if (tipo === '7dias') {
      const seteDiasAtras = new Date()
      seteDiasAtras.setDate(hoje.getDate() - 7)
      return { inicio: seteDiasAtras.toISOString().split('T')[0], fim: hojeStr }
    }
    // 'mes'
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
    return { inicio: primeiroDia.toISOString().split('T')[0], fim: hojeStr }
  }, [])

  const carregarDadosFinanceiros = useCallback(async () => {
    try {
      setCarregando(true)
      const { inicio, fim } = calcularDatasPeriodo(periodo)

      const [resumoData, despesasData] = await Promise.all([
        financeiroService.obterResumo({
          data_inicio: inicio,
          data_fim: fim,
          restaurante_id: restauranteAtivo?.id,
        }),
        financeiroService.listarDespesas({
          data_inicio: inicio,
          data_fim: fim,
          restaurante_id: restauranteAtivo?.id,
        }),
      ])

      setResumo(resumoData)
      setDespesas(despesasData)
    } catch {
      // tratado com fallback
    } finally {
      setCarregando(false)
    }
  }, [periodo, restauranteAtivo?.id, calcularDatasPeriodo])

  useEffect(() => {
    carregarDadosFinanceiros()
  }, [carregarDadosFinanceiros])

  const handleExcluirDespesa = async (id: string) => {
    if (!confirm('Deseja realmente excluir esta despesa operacional?')) return

    try {
      setExcluindoId(id)
      await financeiroService.excluirDespesa(id, restauranteAtivo?.id)
      await carregarDadosFinanceiros()
    } catch {
      alert('Não foi possível excluir a despesa.')
    } finally {
      setExcluindoId(null)
    }
  }

  const formatarMoeda = (valor: number | string | undefined) => {
    if (valor === undefined || valor === null) return 'R$ 0,00'
    const num = typeof valor === 'string' ? parseFloat(valor) : valor
    return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  }

  const saldoNumerico = resumo ? Number(resumo.saldo) : 0
  const totalDespesasNum = resumo ? Number(resumo.total_despesas) : 0

  const categoriasRotulos: Record<string, string> = {
    insumos: 'Insumos & Ingredientes',
    contas_fixas: 'Contas Fixas',
    manutencao: 'Manutenção',
    outros: 'Outros',
  }

  const distribuicaoCategorias = useMemo(() => {
    if (!resumo || !resumo.despesas_por_categoria) return []
    return Object.entries(resumo.despesas_por_categoria).map(([cat, val]) => {
      const valorNum = Number(val)
      const percentual = totalDespesasNum > 0 ? (valorNum / totalDespesasNum) * 100 : 0
      return {
        chave: cat,
        label: categoriasRotulos[cat] || cat,
        valor: valorNum,
        percentual: Math.round(percentual),
      }
    })
  }, [resumo, totalDespesasNum])

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      <TopBar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6 space-y-6">
        {/* Cabeçalho e Filtros de Período */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-zinc-900 tracking-tight">
              Gestão Financeira & Despesas
            </h1>
            <p className="text-sm text-zinc-500">
              Acompanhamento de vendas consolidadas, despesas e fluxo de caixa
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Filtros de período */}
            <div className="inline-flex rounded-xl bg-zinc-200/80 p-1 border border-zinc-200">
              <button
                type="button"
                onClick={() => setPeriodo('hoje')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all min-h-[36px] ${
                  periodo === 'hoje'
                    ? 'bg-white text-zinc-900 shadow-sm'
                    : 'text-zinc-600 hover:text-zinc-900'
                }`}
              >
                Hoje
              </button>
              <button
                type="button"
                onClick={() => setPeriodo('7dias')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all min-h-[36px] ${
                  periodo === '7dias'
                    ? 'bg-white text-zinc-900 shadow-sm'
                    : 'text-zinc-600 hover:text-zinc-900'
                }`}
              >
                7 Dias
              </button>
              <button
                type="button"
                onClick={() => setPeriodo('mes')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all min-h-[36px] ${
                  periodo === 'mes'
                    ? 'bg-white text-zinc-900 shadow-sm'
                    : 'text-zinc-600 hover:text-zinc-900'
                }`}
              >
                Este Mês
              </button>
            </div>

            <Button
              variant="secondary"
              size="sm"
              onClick={carregarDadosFinanceiros}
              isLoading={carregando}
              className="min-h-[40px]"
            >
              <RefreshCw size={16} strokeWidth={2} />
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setDespesaEdicao(null)
                setModalDespesaAberto(true)
              }}
              className="min-h-[40px]"
            >
              <Plus size={16} className="mr-1.5" strokeWidth={2} />
              Nova Despesa
            </Button>
          </div>
        </div>

        {/* Grade de KPIs Financeiros */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <KpiCard
            titulo="Total de Vendas"
            valor={formatarMoeda(resumo?.total_vendas)}
            subtitulo="Receitas recebidas no período"
            icone={TrendingUp}
            tipo="positivo"
          />

          <KpiCard
            titulo="Total de Despesas"
            valor={formatarMoeda(resumo?.total_despesas)}
            subtitulo="Gastos operacionais cadastrados"
            icone={TrendingDown}
            tipo="negativo"
          />

          <KpiCard
            titulo="Saldo Líquido"
            valor={formatarMoeda(resumo?.saldo)}
            subtitulo={saldoNumerico >= 0 ? 'Resultado positivo' : 'Déficit no período'}
            icone={DollarSign}
            tipo={saldoNumerico >= 0 ? 'positivo' : 'negativo'}
          />
        </div>

        {/* Distribuição de Despesas por Categoria */}
        {distribuicaoCategorias.length > 0 && (
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-500">
              Despesas por Categoria
            </h2>

            <div className="space-y-3">
              {distribuicaoCategorias.map((item) => (
                <div key={item.chave} className="space-y-1">
                  <div className="flex justify-between items-center text-xs font-semibold text-zinc-700">
                    <span>{item.label}</span>
                    <span className="tabular-nums">
                      {formatarMoeda(item.valor)} ({item.percentual}%)
                    </span>
                  </div>
                  <div className="w-full bg-zinc-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-zinc-800 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${item.percentual}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Tabela de Despesas Operacionais */}
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-500">
              Lançamentos de Despesas ({despesas.length})
            </h2>
          </div>

          {despesas.length === 0 ? (
            <div className="text-center py-10 text-zinc-500 text-sm">
              Nenhuma despesa registrada para o período selecionado.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-200 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                    <th className="pb-3">Descrição</th>
                    <th className="pb-3">Categoria</th>
                    <th className="pb-3">Data</th>
                    <th className="pb-3 text-right">Valor</th>
                    <th className="pb-3 text-right">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {despesas.map((d) => (
                    <tr key={d.id} className="hover:bg-zinc-50/70 transition-colors">
                      <td className="py-3 font-semibold text-zinc-900 pr-2">
                        {d.descricao}
                      </td>
                      <td className="py-3">
                        <Badge variant="zinc">
                          {categoriasRotulos[d.categoria] || d.categoria}
                        </Badge>
                      </td>
                      <td className="py-3 text-xs text-zinc-500 tabular-nums">
                        <span className="flex items-center gap-1">
                          <Calendar size={13} strokeWidth={2} />
                          {new Date(d.data_pagamento + 'T00:00:00').toLocaleDateString('pt-BR')}
                        </span>
                      </td>
                      <td className="py-3 text-right font-bold text-red-600 tabular-nums">
                        - {formatarMoeda(d.valor)}
                      </td>
                      <td className="py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => {
                              setDespesaEdicao(d)
                              setModalDespesaAberto(true)
                            }}
                            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center"
                            title="Editar despesa"
                          >
                            <Pencil size={15} strokeWidth={2} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleExcluirDespesa(d.id)}
                            disabled={excluindoId === d.id}
                            className="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center"
                            title="Excluir despesa"
                          >
                            <Trash2 size={15} strokeWidth={2} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </main>

      <DespesaModal
        isOpen={modalDespesaAberto}
        onClose={() => setModalDespesaAberto(false)}
        despesaEdicao={despesaEdicao}
        onDespesaSalva={carregarDadosFinanceiros}
      />
    </div>
  )
}
