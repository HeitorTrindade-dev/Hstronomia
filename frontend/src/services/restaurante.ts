import { api } from './api'
import {
  Restaurante,
  RestauranteCreateInput,
  RestaurantePinsUpdateInput,
  RestaurantePublico,
  RestauranteUpdateInput,
} from '../types/restaurante'

export const restauranteService = {
  async obterPorSlug(slug: string): Promise<RestaurantePublico> {
    const response = await api.get<RestaurantePublico>(`/restaurantes/slug/${slug}`)
    return response.data
  },

  async listarMeusRestaurantes(): Promise<Restaurante[]> {
    const response = await api.get<Restaurante[]>('/restaurantes')
    return response.data
  },

  async criarRestaurante(data: RestauranteCreateInput): Promise<Restaurante> {
    const response = await api.post<Restaurante>('/restaurantes', data)
    return response.data
  },

  async atualizarRestaurante(id: string, data: RestauranteUpdateInput): Promise<Restaurante> {
    const response = await api.patch<Restaurante>(`/restaurantes/${id}`, data)
    return response.data
  },

  async atualizarPins(id: string, data: RestaurantePinsUpdateInput): Promise<Restaurante> {
    const response = await api.patch<Restaurante>(`/restaurantes/${id}/pins`, data)
    return response.data
  },
}
