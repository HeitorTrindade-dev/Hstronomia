import { api } from './api'
import { CozinhaPedido, StatusFilaCozinha, StatusItemCozinha } from '../types/cozinha'

export interface ListarPedidosCozinhaParams {
  status?: StatusFilaCozinha
  restaurante_id?: string
  limit?: number
  offset?: number
}

export const cozinhaService = {
  async listarPedidos(params?: ListarPedidosCozinhaParams): Promise<CozinhaPedido[]> {
    const response = await api.get<CozinhaPedido[]>('/cozinha/pedidos', { params })
    return response.data
  },

  async atualizarStatusPedido(
    itemComandaId: string,
    status: StatusItemCozinha,
    restaurante_id?: string
  ): Promise<CozinhaPedido> {
    const response = await api.patch<CozinhaPedido>(
      `/cozinha/pedidos/${itemComandaId}/status`,
      { status },
      { params: { restaurante_id } }
    )
    return response.data
  },
}
