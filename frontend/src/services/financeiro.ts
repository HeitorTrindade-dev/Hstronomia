import { api } from './api'
import {
  CategoriaDespesa,
  Despesa,
  DespesaCreateInput,
  DespesaUpdateInput,
  ResumoFinanceiro,
} from '../types/financeiro'

export interface ListarDespesasParams {
  data_inicio?: string
  data_fim?: string
  categoria?: CategoriaDespesa
  restaurante_id?: string
  limit?: number
  offset?: number
}

export const financeiroService = {
  async obterResumo(params?: {
    data_inicio?: string
    data_fim?: string
    restaurante_id?: string
  }): Promise<ResumoFinanceiro> {
    const response = await api.get<ResumoFinanceiro>('/financeiro/resumo', { params })
    return response.data
  },

  async listarDespesas(params?: ListarDespesasParams): Promise<Despesa[]> {
    const response = await api.get<Despesa[]>('/financeiro/despesas', { params })
    return response.data
  },

  async criarDespesa(data: DespesaCreateInput, restaurante_id?: string): Promise<Despesa> {
    const response = await api.post<Despesa>('/financeiro/despesas', data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async atualizarDespesa(
    id: string,
    data: DespesaUpdateInput,
    restaurante_id?: string
  ): Promise<Despesa> {
    const response = await api.patch<Despesa>(`/financeiro/despesas/${id}`, data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async excluirDespesa(id: string, restaurante_id?: string): Promise<void> {
    await api.delete(`/financeiro/despesas/${id}`, {
      params: { restaurante_id },
    })
  },
}
