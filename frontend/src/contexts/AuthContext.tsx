import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import {
  AuthMeResponse,
  Dono,
  LoginDonoCredentials,
  LoginOperacionalCredentials,
  Restaurante,
  UserRole,
} from '../types/auth'
import { authService } from '../services/auth'
import {
  TOKEN_STORAGE_KEY,
  ROLE_STORAGE_KEY,
  RESTAURANTE_STORAGE_KEY,
} from '../services/api'

interface AuthContextType {
  token: string | null
  role: UserRole | null
  user: Dono | null
  restaurante: Restaurante | null
  restauranteAtivo: Restaurante | null
  isAuthenticated: boolean
  isLoading: boolean
  loginDono: (credentials: LoginDonoCredentials) => Promise<void>
  loginOperacional: (credentials: LoginOperacionalCredentials) => Promise<void>
  logout: () => void
  setRestauranteAtivo: (restaurante: Restaurante) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY))
  const [role, setRole] = useState<UserRole | null>(() => {
    return (localStorage.getItem(ROLE_STORAGE_KEY) as UserRole) || null
  })
  const [user, setUser] = useState<Dono | null>(null)
  const [restaurante, setRestaurante] = useState<Restaurante | null>(() => {
    const salvo = localStorage.getItem(RESTAURANTE_STORAGE_KEY)
    if (salvo) {
      try {
        return JSON.parse(salvo)
      } catch {
        return null
      }
    }
    return null
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(ROLE_STORAGE_KEY)
    localStorage.removeItem(RESTAURANTE_STORAGE_KEY)
    setToken(null)
    setRole(null)
    setUser(null)
    setRestaurante(null)
  }, [])

  // Restauração de sessão ao carregar a página via /auth/me
  useEffect(() => {
    const restaurarSessao = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
      if (!storedToken) {
        setIsLoading(false)
        return
      }

      try {
        const dadosMe: AuthMeResponse = await authService.getMe()
        setRole(dadosMe.role)
        localStorage.setItem(ROLE_STORAGE_KEY, dadosMe.role)

        if (dadosMe.dono) {
          setUser(dadosMe.dono)
        }

        if (dadosMe.restaurante_id && dadosMe.restaurante_nome) {
          const restInfo: Restaurante = {
            id: dadosMe.restaurante_id,
            nome: dadosMe.restaurante_nome,
            slug: dadosMe.restaurante_slug || '',
          }
          setRestaurante(restInfo)
          localStorage.setItem(RESTAURANTE_STORAGE_KEY, JSON.stringify(restInfo))
        }
      } catch {
        // Se o token for inválido ou expirado, limpa o estado
        logout()
      } finally {
        setIsLoading(false)
      }
    }

    restaurarSessao()
  }, [logout])

  const loginDono = async (credentials: LoginDonoCredentials) => {
    setIsLoading(true)
    try {
      const data = await authService.loginDono(credentials)
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
      localStorage.setItem(ROLE_STORAGE_KEY, data.role)

      setToken(data.access_token)
      setRole(data.role)
      if (data.dono) {
        setUser(data.dono)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const loginOperacional = async (credentials: LoginOperacionalCredentials) => {
    setIsLoading(true)
    try {
      const data = await authService.loginOperacional(credentials)
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
      localStorage.setItem(ROLE_STORAGE_KEY, data.role)

      setToken(data.access_token)
      setRole(data.role)

      if (data.restaurante_id && data.restaurante_nome) {
        const restInfo: Restaurante = {
          id: data.restaurante_id,
          nome: data.restaurante_nome,
          slug: data.restaurante_slug || credentials.slug,
        }
        setRestaurante(restInfo)
        localStorage.setItem(RESTAURANTE_STORAGE_KEY, JSON.stringify(restInfo))
      }
    } finally {
      setIsLoading(false)
    }
  }

  const setRestauranteAtivo = (rest: Restaurante) => {
    setRestaurante(rest)
    localStorage.setItem(RESTAURANTE_STORAGE_KEY, JSON.stringify(rest))
  }

  const value: AuthContextType = {
    token,
    role,
    user,
    restaurante,
    restauranteAtivo: restaurante,
    isAuthenticated: Boolean(token && role),
    isLoading,
    loginDono,
    loginOperacional,
    logout,
    setRestauranteAtivo,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth deve ser utilizado dentro de um AuthProvider')
  }
  return context
}
