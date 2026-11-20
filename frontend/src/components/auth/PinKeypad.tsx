import { useEffect, useCallback } from 'react'
import { Delete, Check } from 'lucide-react'

export interface PinKeypadProps {
  pin: string
  onChange: (pin: string) => void
  onSubmit?: () => void
  maxLength?: number
  disabled?: boolean
  isLoading?: boolean
}

export function PinKeypad({
  pin,
  onChange,
  onSubmit,
  maxLength = 4,
  disabled = false,
  isLoading = false,
}: PinKeypadProps) {
  const handleDigit = useCallback(
    (digit: string) => {
      if (disabled || isLoading) return
      if (pin.length < maxLength) {
        onChange(pin + digit)
      }
    },
    [pin, maxLength, disabled, isLoading, onChange]
  )

  const handleBackspace = useCallback(() => {
    if (disabled || isLoading) return
    if (pin.length > 0) {
      onChange(pin.slice(0, -1))
    }
  }, [pin, disabled, isLoading, onChange])

  const handleClear = useCallback(() => {
    if (disabled || isLoading) return
    onChange('')
  }, [disabled, isLoading, onChange])

  // Suporte a teclado físico quando o componente estiver na tela
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (disabled || isLoading) return

      if (e.key >= '0' && e.key <= '9') {
        handleDigit(e.key)
      } else if (e.key === 'Backspace') {
        handleBackspace()
      } else if (e.key === 'Enter' && onSubmit && pin.length >= 4) {
        onSubmit()
      } else if (e.key === 'Escape') {
        handleClear()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleDigit, handleBackspace, handleClear, onSubmit, pin.length, disabled, isLoading])

  const digits = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

  return (
    <div className="w-full max-w-xs mx-auto flex flex-col items-center select-none space-y-4">
      {/* Indicadores visuais dos dígitos do PIN */}
      <div className="flex items-center justify-center gap-3 py-2" aria-label={`PIN com ${pin.length} dígitos informados`}>
        {Array.from({ length: maxLength }).map((_, idx) => {
          const isFilled = idx < pin.length
          return (
            <div
              key={idx}
              className={`w-3.5 h-3.5 rounded-full border transition-all ${
                isFilled
                  ? 'bg-red-600 border-red-600 scale-110 shadow-sm'
                  : 'bg-zinc-100 dark:bg-zinc-800 border-zinc-300 dark:border-zinc-700'
              }`}
            />
          )
        })}
      </div>

      {/* Grade do Teclado Numérico Touch */}
      <div className="grid grid-cols-3 gap-2.5 w-full">
        {digits.map((num) => (
          <button
            key={num}
            type="button"
            disabled={disabled || isLoading || pin.length >= maxLength}
            onClick={() => handleDigit(num)}
            className="h-14 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-xl font-semibold shadow-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 active:bg-zinc-100 dark:active:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            {num}
          </button>
        ))}

        {/* Botão Limpar / Apagar */}
        <button
          type="button"
          disabled={disabled || isLoading || pin.length === 0}
          onClick={handleBackspace}
          aria-label="Apagar último dígito"
          className="h-14 rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 flex items-center justify-center shadow-sm hover:bg-zinc-100 dark:hover:bg-zinc-800 active:bg-zinc-200 dark:active:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <Delete className="w-5 h-5" strokeWidth={2} />
        </button>

        {/* Dígito 0 */}
        <button
          type="button"
          disabled={disabled || isLoading || pin.length >= maxLength}
          onClick={() => handleDigit('0')}
          className="h-14 rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 text-xl font-semibold shadow-sm hover:bg-zinc-50 dark:hover:bg-zinc-800 active:bg-zinc-100 dark:active:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          0
        </button>

        {/* Botão Confirmar */}
        <button
          type="button"
          disabled={disabled || isLoading || pin.length < 4}
          onClick={onSubmit}
          aria-label="Confirmar PIN"
          className="h-14 rounded-md bg-red-600 text-white flex items-center justify-center shadow-sm hover:bg-red-700 active:bg-red-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <Check className="w-5 h-5" strokeWidth={2} />
        </button>
      </div>
    </div>
  )
}
