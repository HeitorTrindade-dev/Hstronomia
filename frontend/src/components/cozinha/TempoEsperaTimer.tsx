import React, { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'

interface TempoEsperaTimerProps {
  criadoEm: string
}

export const TempoEsperaTimer: React.FC<TempoEsperaTimerProps> = ({ criadoEm }) => {
  const [minutos, setMinutos] = useState(0)

  useEffect(() => {
    const calcular = () => {
      const inicio = new Date(criadoEm).getTime()
      const agora = Date.now()
      const diffMin = Math.floor((agora - inicio) / 60000)
      setMinutos(Math.max(0, diffMin))
    }

    calcular()
    const timer = setInterval(calcular, 10000)
    return () => clearInterval(timer)
  }, [criadoEm])

  let corClasses = 'text-emerald-400 bg-emerald-950/50 border-emerald-800'
  if (minutos >= 20) {
    corClasses = 'text-red-400 bg-red-950/50 border-red-700 animate-pulse'
  } else if (minutos >= 10) {
    corClasses = 'text-amber-400 bg-amber-950/50 border-amber-800'
  }

  const formatarTempo = () => {
    if (minutos < 1) return '< 1 min'
    if (minutos < 60) return `${minutos} min`
    const horas = Math.floor(minutos / 60)
    const resto = minutos % 60
    return `${horas}h ${resto}m`
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-bold tabular-nums ${corClasses}`}
    >
      <Clock size={12} strokeWidth={2.5} />
      <span>{formatarTempo()}</span>
    </div>
  )
}
