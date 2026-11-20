import { api } from './api'
import { RestaurantePublico } from '../types/restaurante'

export const restauranteService = {
  async obterPorSlug(slug: string): Promise<RestaurantePublico> {
    const response = await api.get<RestaurantePublico>(`/restaurantes/slug/${slug}`)
    return response.data
  },
}
