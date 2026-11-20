import { api } from './api'
import {
  Comanda,
  ComandaCreateInput,
  ComandaFecharInput,
  ComandaPrevia,
  ItemComanda,
  ItemComandaCreateInput,
  ItemComandaUpdateInput,
  StatusComanda,
} from '../types/comanda'

export interface ListarComandasParams {
  restaurante_id?: string
  status?: StatusComanda
  numero_mesa?: number
  limit?: number
  offset?: number
}

export const comandaService = {
  async listarComandas(params?: ListarComandasParams): Promise<Comanda[]> {
    const response = await api.get<Comanda[]>('/comandas', { params })
    return response.data
  },

  async obterComanda(id: string, restaurante_id?: string): Promise<Comanda> {
    const response = await api.get<Comanda>(`/comandas/${id}`, {
      params: { restaurante_id },
    })
    return response.data
  },

  async abrirComanda(data: ComandaCreateInput, restaurante_id?: string): Promise<Comanda> {
    const response = await api.post<Comanda>('/comandas', data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async adicionarItem(
    comandaId: string,
    data: ItemComandaCreateInput,
    restaurante_id?: string
  ): Promise<ItemComanda> {
    const response = await api.post<ItemComanda>(`/comandas/${comandaId}/itens`, data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async atualizarItem(
    comandaId: string,
    itemId: string,
    data: ItemComandaUpdateInput,
    restaurante_id?: string
  ): Promise<ItemComanda> {
    const response = await api.patch<ItemComanda>(
      `/comandas/${comandaId}/itens/${itemId}`,
      data,
      { params: { restaurante_id } }
    )
    return response.data
  },

  async removerItem(
    comandaId: string,
    itemId: string,
    restaurante_id?: string
  ): Promise<{ status: string; item_id: string }> {
    const response = await api.delete<{ status: string; item_id: string }>(
      `/comandas/${comandaId}/itens/${itemId}`,
      { params: { restaurante_id } }
    )
    return response.data
  },

  async obterPrevia(
    comandaId: string,
    params?: { incluir_taxa_servico?: boolean; desconto?: number; restaurante_id?: string }
  ): Promise<ComandaPrevia> {
    const response = await api.get<ComandaPrevia>(`/comandas/${comandaId}/previa`, {
      params: {
        incluir_taxa_servico: params?.incluir_taxa_servico ?? true,
        desconto: params?.desconto ?? 0,
        restaurante_id: params?.restaurante_id,
      },
    })
    return response.data
  },

  async fecharComanda(
    comandaId: string,
    data: ComandaFecharInput,
    restaurante_id?: string
  ): Promise<Comanda> {
    const response = await api.post<Comanda>(`/comandas/${comandaId}/fechar`, data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async cancelarComanda(
    comandaId: string,
    restaurante_id?: string
  ): Promise<Comanda> {
    const response = await api.post<Comanda>(
      `/comandas/${comandaId}/cancelar`,
      null,
      { params: { restaurante_id } }
    )
    return response.data
  },
}
