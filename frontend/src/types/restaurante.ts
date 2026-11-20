export interface RestaurantePublico {
  id: string
  nome: string
  slug: string
}

export interface Restaurante {
  id: string
  dono_id: string
  nome: string
  slug: string
  codigo_garcom: string
  codigo_cozinha: string
  criado_em: string
}

export interface RestauranteCreateInput {
  nome: string
  slug: string
  codigo_garcom: string
  codigo_cozinha: string
}

export interface RestauranteUpdateInput {
  nome?: string
  slug?: string
}

export interface RestaurantePinsUpdateInput {
  codigo_garcom?: string
  codigo_cozinha?: string
}
