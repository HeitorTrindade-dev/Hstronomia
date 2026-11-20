import { api } from './api'
import {
  AuthMeResponse,
  CadastroDonoData,
  Dono,
  LoginDonoCredentials,
  LoginOperacionalCredentials,
  TokenResponse,
} from '../types/auth'

export const authService = {
  async loginDono(credentials: LoginDonoCredentials): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials)
    return response.data
  },

  async cadastrarDono(data: CadastroDonoData): Promise<Dono> {
    const response = await api.post<Dono>('/auth/cadastrar', data)
    return response.data
  },

  async loginOperacional(credentials: LoginOperacionalCredentials): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/operacional', credentials)
    return response.data
  },

  async getMe(): Promise<AuthMeResponse> {
    const response = await api.get<AuthMeResponse>('/auth/me')
    return response.data
  },
}
