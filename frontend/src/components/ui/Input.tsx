import React, { forwardRef, useId } from 'react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      id,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const generatedId = useId()
    const inputId = id || generatedId
    const errorId = `${inputId}-error`
    const hintId = `${inputId}-hint`

    const describedBy = error ? errorId : hint ? hintId : undefined

    return (
      <div className="w-full space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-medium text-zinc-700 dark:text-zinc-300"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-2.5 flex items-center pointer-events-none text-zinc-400 dark:text-zinc-500">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={Boolean(error)}
            aria-describedby={describedBy}
            className={`w-full h-9 rounded-md text-sm border bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-500 transition-colors focus:outline-none focus:ring-2 disabled:opacity-50 disabled:bg-zinc-100 dark:disabled:bg-zinc-800 disabled:cursor-not-allowed ${
              leftIcon ? 'pl-8' : 'px-3'
            } ${rightIcon ? 'pr-8' : 'px-3'} ${
              error
                ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500 text-red-900 dark:text-red-200'
                : 'border-zinc-300 dark:border-zinc-700 focus:border-red-600 focus:ring-red-500/20'
            } ${className}`}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-2.5 flex items-center text-zinc-400 dark:text-zinc-500">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <p id={errorId} className="text-xs text-red-600 dark:text-red-400">
            {error}
          </p>
        ) : hint ? (
          <p id={hintId} className="text-xs text-zinc-500 dark:text-zinc-400">
            {hint}
          </p>
        ) : null}
      </div>
    )
  }
)

Input.displayName = 'Input'
