import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

export const TOKEN_STORAGE_KEY = '@hstronomia:token'
export const ROLE_STORAGE_KEY = '@hstronomia:role'
export const RESTAURANTE_STORAGE_KEY = '@hstronomia:restaurante'

const baseURL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor de Requisição: Injeta o Bearer Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor de Resposta: Trata expiração de sessão (401)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const isAuthEndpoint =
        error.config?.url?.includes('/auth/login') ||
        error.config?.url?.includes('/auth/operacional') ||
        error.config?.url?.includes('/auth/cadastrar')

      // Só limpa e redireciona se for erro de token expirado em rotas normais
      if (!isAuthEndpoint) {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
        localStorage.removeItem(ROLE_STORAGE_KEY)
        localStorage.removeItem(RESTAURANTE_STORAGE_KEY)

        // Se estivermos em uma rota protegida, redireciona
        if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/acesso')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
