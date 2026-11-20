import { api } from './api'
import { Item, ItemCreateInput, ItemUpdateInput } from '../types/cardapio'

export interface ListarItensParams {
  restaurante_id: string
  incluir_inativos?: boolean
  apenas_disponiveis?: boolean
  limit?: number
  offset?: number
}

export const cardapioService = {
  async listarItens(params: ListarItensParams): Promise<Item[]> {
    const response = await api.get<Item[]>('/itens', {
      params: {
        restaurante_id: params.restaurante_id,
        incluir_inativos: params.incluir_inativos ?? false,
        apenas_disponiveis: params.apenas_disponiveis ?? false,
        limit: params.limit ?? 100,
        offset: params.offset ?? 0,
      },
    })
    return response.data
  },

  async criarItem(restaurante_id: string, data: ItemCreateInput): Promise<Item> {
    const response = await api.post<Item>('/itens', data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async atualizarItem(restaurante_id: string, item_id: string, data: ItemUpdateInput): Promise<Item> {
    const response = await api.put<Item>(`/itens/${item_id}`, data, {
      params: { restaurante_id },
    })
    return response.data
  },

  async alterarDisponibilidade(restaurante_id: string, item_id: string, disponivel: boolean): Promise<Item> {
    const response = await api.patch<Item>(
      `/itens/${item_id}/disponibilidade`,
      { disponivel },
      { params: { restaurante_id } }
    )
    return response.data
  },

  async desativarItem(restaurante_id: string, item_id: string): Promise<Item> {
    const response = await api.delete<Item>(`/itens/${item_id}`, {
      params: { restaurante_id },
    })
    return response.data
  },

  async reativarItem(restaurante_id: string, item_id: string, disponivel: boolean = true): Promise<Item> {
    const response = await api.patch<Item>(
      `/itens/${item_id}/reativar`,
      { disponivel },
      { params: { restaurante_id } }
    )
    return response.data
  },
}
