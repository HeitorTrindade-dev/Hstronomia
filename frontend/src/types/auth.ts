export type UserRole = 'dono' | 'garcom' | 'cozinha'

export interface Dono {
  id: string
  nome: string
  email: string
  criado_em: string
}

export interface Restaurante {
  id: string
  nome: string
  slug: string
}

export interface LoginDonoCredentials {
  email: string
  senha: string
}

export interface CadastroDonoData {
  nome: string
  email: string
  senha: string
}

export interface LoginOperacionalCredentials {
  slug: string
  pin: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  role: UserRole
  dono?: Dono | null
  restaurante_id?: string | null
  restaurante_nome?: string | null
  restaurante_slug?: string | null
}

export interface AuthMeResponse {
  role: UserRole
  dono?: Dono | null
  restaurante_id?: string | null
  restaurante_nome?: string | null
  restaurante_slug?: string | null
}

export interface UserSession {
  token: string | null
  role: UserRole | null
  user: Dono | null
  restaurante: Restaurante | null
  isAuthenticated: boolean
  isLoading: boolean
}
