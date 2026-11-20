import React from 'react'
import { LucideIcon } from 'lucide-react'
import { Card } from '../ui/Card'

interface KpiCardProps {
  titulo: string
  valor: string
  subtitulo?: string
  icone: LucideIcon
  tipo?: 'positivo' | 'negativo' | 'neutro'
}

export const KpiCard: React.FC<KpiCardProps> = ({
  titulo,
  valor,
  subtitulo,
  icone: Icone,
  tipo = 'neutro',
}) => {
  let corValor = 'text-zinc-900'
  let bgIcone = 'bg-zinc-100 text-zinc-600'

  if (tipo === 'positivo') {
    corValor = 'text-emerald-600'
    bgIcone = 'bg-emerald-50 text-emerald-600'
  } else if (tipo === 'negativo') {
    corValor = 'text-red-600'
    bgIcone = 'bg-red-50 text-red-600'
  }

  return (
    <Card className="p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-zinc-500">
          {titulo}
        </span>
        <div className={`p-2 rounded-xl ${bgIcone}`}>
          <Icone size={18} strokeWidth={2} />
        </div>
      </div>

      <div className="mt-3">
        <span className={`text-2xl sm:text-3xl font-black tabular-nums tracking-tight ${corValor}`}>
          {valor}
        </span>
        {subtitulo && (
          <p className="text-xs text-zinc-500 mt-1 font-medium">{subtitulo}</p>
        )}
      </div>
    </Card>
  )
}
