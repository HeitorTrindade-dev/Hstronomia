import React from 'react'

export type BadgeVariant = 'emerald' | 'amber' | 'sky' | 'red' | 'zinc'
export type BadgeSize = 'sm' | 'md'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  size?: BadgeSize
  withDot?: boolean
}

const variantStyles: Record<BadgeVariant, { container: string; dot: string }> = {
  emerald: {
    container:
      'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800',
    dot: 'bg-emerald-500',
  },
  amber: {
    container:
      'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800',
    dot: 'bg-amber-500',
  },
  sky: {
    container:
      'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-400 dark:border-sky-800',
    dot: 'bg-sky-500',
  },
  red: {
    container:
      'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800',
    dot: 'bg-red-500',
  },
  zinc: {
    container:
      'bg-zinc-100 text-zinc-700 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700',
    dot: 'bg-zinc-400',
  },
}

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'text-xs py-0.5 px-2 gap-1 rounded font-normal',
  md: 'text-xs py-1 px-2.5 gap-1.5 rounded-md font-medium',
}

export function Badge({
  variant = 'zinc',
  size = 'md',
  withDot = false,
  className = '',
  children,
  ...props
}: BadgeProps) {
  const currentVariant = variantStyles[variant]

  return (
    <span
      className={`inline-flex items-center border select-none tabular-nums ${currentVariant.container} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {withDot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${currentVariant.dot}`}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  )
}
