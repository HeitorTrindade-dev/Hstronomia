import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className = '', children, ...props }: CardProps) {
  return (
    <div
      className={`rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm transition-colors ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardHeader({ className = '', children, ...props }: CardHeaderProps) {
  return (
    <div className={`p-4 border-b border-zinc-100 dark:border-zinc-800/80 ${className}`} {...props}>
      {children}
    </div>
  )
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

export function CardTitle({ className = '', children, ...props }: CardTitleProps) {
  return (
    <h3 className={`text-base font-semibold text-zinc-900 dark:text-zinc-100 ${className}`} {...props}>
      {children}
    </h3>
  )
}

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

export function CardDescription({ className = '', children, ...props }: CardDescriptionProps) {
  return (
    <p className={`text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 ${className}`} {...props}>
      {children}
    </p>
  )
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardContent({ className = '', children, ...props }: CardContentProps) {
  return (
    <div className={`p-4 ${className}`} {...props}>
      {children}
    </div>
  )
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

export function CardFooter({ className = '', children, ...props }: CardFooterProps) {
  return (
    <div
      className={`p-4 pt-0 border-t border-zinc-100 dark:border-zinc-800/80 mt-4 flex items-center justify-end gap-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}
