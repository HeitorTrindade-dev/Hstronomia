import React, { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 border border-transparent shadow-sm focus-visible:ring-red-500',
  secondary:
    'bg-white text-zinc-700 border border-zinc-300 hover:bg-zinc-50 active:bg-zinc-100 shadow-sm focus-visible:ring-zinc-400 dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700 dark:hover:bg-zinc-700',
  danger:
    'bg-red-700 text-white hover:bg-red-800 active:bg-red-900 border border-transparent shadow-sm focus-visible:ring-red-600',
  ghost:
    'bg-transparent text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 focus-visible:ring-zinc-400 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-2.5 text-xs gap-1.5 rounded-md font-medium',
  md: 'h-9 px-3.5 text-sm gap-2 rounded-md font-medium',
  lg: 'h-10 px-4 text-base gap-2 rounded-md font-medium',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      className = '',
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={`inline-flex items-center justify-center transition-colors select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    )
  }
)

Button.displayName = 'Button'
