import React from 'react'
import { LucideIcon } from 'lucide-react'
import { Button, ButtonVariant } from './Button'

export interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
    variant?: ButtonVariant
    leftIcon?: React.ReactNode
  }
  className?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center border border-dashed border-zinc-200 dark:border-zinc-800 rounded-md bg-zinc-50/50 dark:bg-zinc-900/50 ${className}`}
    >
      <div className="w-10 h-10 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 flex items-center justify-center mb-3">
        <Icon className="w-5 h-5" strokeWidth={2} />
      </div>
      <h4 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h4>
      {description && (
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-xs">
          {description}
        </p>
      )}
      {action && (
        <div className="mt-4">
          <Button
            size="sm"
            variant={action.variant || 'primary'}
            onClick={action.onClick}
            leftIcon={action.leftIcon}
          >
            {action.label}
          </Button>
        </div>
      )}
    </div>
  )
}
