import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { UtensilsCrossed, LogOut, Moon, Sun, Store, BookOpen, LayoutDashboard } from 'lucide-react'
import { Badge, BadgeVariant } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Restaurante } from '../../types/restaurante'

export type UserRole = 'dono' | 'garcom' | 'cozinha'

export interface TopBarProps {
  restaurantName?: string
  role?: UserRole
  userName?: string
  onLogout?: () => void
  actions?: React.ReactNode
  isDarkMode?: boolean
  onToggleDarkMode?: () => void
  restaurantesDisponiveis?: Restaurante[]
  onSelectRestaurante?: (restaurante: Restaurante) => void
}

const roleBadgeConfig: Record<UserRole, { label: string; variant: BadgeVariant }> = {
  dono: { label: 'Dono', variant: 'zinc' },
  garcom: { label: 'Garçom', variant: 'sky' },
  cozinha: { label: 'Cozinha KDS', variant: 'amber' },
}

export function TopBar({
  restaurantName,
  role,
  userName,
  onLogout,
  actions,
  isDarkMode,
  onToggleDarkMode,
  restaurantesDisponiveis = [],
  onSelectRestaurante,
}: TopBarProps) {
  const roleConfig = role ? roleBadgeConfig[role] : null
  const location = useLocation()

  return (
    <header className="h-14 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-40 px-4 flex items-center justify-between select-none">
      {/* Lado Esquerdo: Marca & Navegação / Restaurante Ativo */}
      <div className="flex items-center gap-3">
        <Link to={role === 'dono' ? '/admin' : role === 'garcom' ? '/garcom' : role === 'cozinha' ? '/cozinha' : '/'} className="flex items-center gap-2 hover:opacity-90 transition-opacity">
          <div className="w-8 h-8 rounded-md bg-red-50 dark:bg-red-950/40 text-red-600 flex items-center justify-center border border-red-100 dark:border-red-900/50">
            <UtensilsCrossed className="w-4 h-4" strokeWidth={2} />
          </div>
          <span className="text-base font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            Hstronomia
          </span>
        </Link>

        {/* Seletor ou Exibição do Restaurante Ativo */}
        {restaurantesDisponiveis.length > 1 && onSelectRestaurante ? (
          <div className="flex items-center gap-1.5 ml-2">
            <span className="text-zinc-300 dark:text-zinc-700 font-light">/</span>
            <select
              aria-label="Selecionar restaurante ativo"
              value={restaurantName}
              onChange={(e) => {
                const encontrado = restaurantesDisponiveis.find((r) => r.nome === e.target.value)
                if (encontrado) onSelectRestaurante(encontrado)
              }}
              className="h-7 text-xs font-medium text-zinc-700 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 px-2 rounded border border-zinc-300 dark:border-zinc-700 focus:outline-none focus:ring-1 focus:ring-red-500 cursor-pointer"
            >
              {restaurantesDisponiveis.map((rest) => (
                <option key={rest.id} value={rest.nome}>
                  {rest.nome}
                </option>
              ))}
            </select>
          </div>
        ) : restaurantName ? (
          <div className="flex items-center gap-1.5 ml-2">
            <span className="text-zinc-300 dark:text-zinc-700 font-light">/</span>
            <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded border border-zinc-200 dark:border-zinc-700">
              {restaurantName}
            </span>
          </div>
        ) : null}

        {/* Links de navegação para Dono */}
        {role === 'dono' && (
          <nav className="hidden md:flex items-center gap-1 ml-4 border-l border-zinc-200 dark:border-zinc-800 pl-4">
            <Link
              to="/admin"
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                location.pathname === '/admin'
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Visão Geral</span>
            </Link>

            <Link
              to="/admin/cardapio"
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                location.pathname.startsWith('/admin/cardapio')
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Cardápio</span>
            </Link>

            <Link
              to="/admin/restaurantes"
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                location.pathname.startsWith('/admin/restaurantes')
                  ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                  : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
              }`}
            >
              <Store className="w-3.5 h-3.5" />
              <span>Restaurantes & PINs</span>
            </Link>
          </nav>
        )}
      </div>

      {/* Lado Direito: Ações, Perfil, Tema e Logout */}
      <div className="flex items-center gap-2.5">
        {actions && <div className="flex items-center gap-1.5 mr-1">{actions}</div>}

        {roleConfig && (
          <Badge variant={roleConfig.variant} size="sm" withDot>
            {roleConfig.label}
          </Badge>
        )}

        {userName && (
          <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400 hidden sm:inline-block">
            {userName}
          </span>
        )}

        {onToggleDarkMode && (
          <button
            type="button"
            onClick={onToggleDarkMode}
            aria-label={isDarkMode ? 'Alternar para tema claro' : 'Alternar para tema escuro'}
            className="p-1.5 text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        )}

        {onLogout && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            leftIcon={<LogOut className="w-3.5 h-3.5" />}
            className="text-zinc-500 hover:text-red-600 dark:hover:text-red-400"
          >
            Sair
          </Button>
        )}
      </div>
    </header>
  )
}
