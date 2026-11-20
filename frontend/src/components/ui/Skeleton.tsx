import React from 'react'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'rect' | 'circle' | 'text'
}

export function Skeleton({
  variant = 'rect',
  className = '',
  ...props
}: SkeletonProps) {
  const baseStyles = 'animate-pulse bg-zinc-200 dark:bg-zinc-800'

  if (variant === 'circle') {
    return (
      <div
        className={`${baseStyles} rounded-full shrink-0 ${className}`}
        aria-hidden="true"
        {...props}
      />
    )
  }

  if (variant === 'text') {
    return (
      <div
        className={`${baseStyles} h-4 w-full rounded ${className}`}
        aria-hidden="true"
        {...props}
      />
    )
  }

  return (
    <div
      className={`${baseStyles} rounded-md ${className}`}
      aria-hidden="true"
      {...props}
    />
  )
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div
      className={`p-4 border border-zinc-200 dark:border-zinc-800 rounded-md bg-white dark:bg-zinc-900 space-y-3 ${className}`}
      aria-hidden="true"
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-5 w-16" />
      </div>
      <Skeleton className="h-4 w-2/3" />
      <div className="pt-2 flex justify-between items-center border-t border-zinc-100 dark:border-zinc-800">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  )
}

export function SkeletonTableRow({ columns = 4 }: { columns?: number }) {
  return (
    <div
      className="flex items-center justify-between p-3 border-b border-zinc-100 dark:border-zinc-800/80 gap-4"
      aria-hidden="true"
    >
      {Array.from({ length: columns }).map((_, index) => (
        <Skeleton
          key={index}
          className={`h-4 ${index === 0 ? 'w-1/4' : index === columns - 1 ? 'w-20' : 'w-1/6'}`}
        />
      ))}
    </div>
  )
}
