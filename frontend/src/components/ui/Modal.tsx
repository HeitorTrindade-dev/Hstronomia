import React, { useEffect, useId, useRef } from 'react'
import { X } from 'lucide-react'

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
  size?: ModalSize
  hideCloseButton?: boolean
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  hideCloseButton = false,
}: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const descriptionId = useId()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (isOpen && !dialog.open) {
      dialog.showModal()
    } else if (!isOpen && dialog.open) {
      dialog.close()
    }
  }, [isOpen])

  // Escuta o evento nativo 'close' do dialog (disparado por Esc ou comando de fechar)
  const handleNativeClose = () => {
    if (isOpen) {
      onClose()
    }
  }

  // Fallback de light-dismiss (clique no backdrop) para navegadores sem closedby nativo
  const handlePointerDown = (e: React.PointerEvent<HTMLDialogElement>) => {
    const dialog = dialogRef.current
    if (!dialog) return

    const rect = dialog.getBoundingClientRect()
    const isOutside =
      e.clientX < rect.left ||
      e.clientX > rect.right ||
      e.clientY < rect.top ||
      e.clientY > rect.bottom

    if (isOutside) {
      onClose()
    }
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={handleNativeClose}
      onPointerDown={handlePointerDown}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      {...({ closedby: 'any' } as Record<string, string>)}
      className={`w-full ${sizeStyles[size]} rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 p-0 shadow-xl m-auto focus:outline-none transition-all`}
    >
      <div className="flex items-center justify-between p-4 border-b border-zinc-100 dark:border-zinc-800/80">
        <div>
          <h2 id={titleId} className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {title}
          </h2>
          {description && (
            <p id={descriptionId} className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              {description}
            </p>
          )}
        </div>
        {!hideCloseButton && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar diálogo"
            className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="p-4">{children}</div>
    </dialog>
  )
}
