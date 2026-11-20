import React from 'react'
import { UtensilsCrossed, LogOut, Moon, Sun } from 'lucide-react'
import { Badge, BadgeVariant } from '../ui/Badge'
import { Button } from '../ui/Button'

export type UserRole = 'dono' | 'garcom' | 'cozinha'

export interface TopBarProps {
  restaurantName?: string
  role?: UserRole
  userName?: string
  onLogout?: () => void
  actions?: React.ReactNode
  isDarkMode?: boolean
  onToggleDarkMode?: () => void
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
}: TopBarProps) {
  const roleConfig = role ? roleBadgeConfig[role] : null

  return (
    <header className="h-14 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 sticky top-0 z-40 px-4 flex items-center justify-between select-none">
      {/* Lado Esquerdo: Marca & Restaurante Ativo */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-red-50 dark:bg-red-950/40 text-red-600 flex items-center justify-center border border-red-100 dark:border-red-900/50">
            <UtensilsCrossed className="w-4 h-4" strokeWidth={2} />
          </div>
          <span className="text-base font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
            Hstronomia
          </span>
        </div>

        {restaurantName && (
          <>
            <span className="text-zinc-300 dark:text-zinc-700 font-light">/</span>
            <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 px-2 py-0.5 rounded border border-zinc-200 dark:border-zinc-700">
              {restaurantName}
            </span>
          </>
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
