import React, { useState } from 'react'
import { Flame, CheckCircle, BellRing } from 'lucide-react'
import { CozinhaPedido, StatusItemCozinha } from '../../types/cozinha'
import { TempoEsperaTimer } from './TempoEsperaTimer'
import { Button } from '../ui/Button'

interface PedidoCardProps {
  pedido: CozinhaPedido
  onAtualizarStatus: (pedidoId: string, novoStatus: StatusItemCozinha) => Promise<void>
}

export const PedidoCard: React.FC<PedidoCardProps> = ({
  pedido,
  onAtualizarStatus,
}) => {
  const [atualizando, setAtualizando] = useState(false)

  const handleAvançar = async (proximoStatus: StatusItemCozinha) => {
    try {
      setAtualizando(true)
      await onAtualizarStatus(pedido.id, proximoStatus)
    } finally {
      setAtualizando(false)
    }
  }

  const tituloOrigem = pedido.tipo_atendimento === 'mesa'
    ? `Mesa ${pedido.numero_mesa}`
    : pedido.tipo_atendimento === 'viagem'
    ? 'Viagem'
    : 'Balcão'

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex flex-col justify-between shadow-lg space-y-3.5 hover:border-zinc-700 transition-colors">
      {/* Cabeçalho do Card */}
      <div className="flex items-start justify-between gap-2 border-b border-zinc-800/80 pb-2.5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-black text-white tracking-wide">
              {tituloOrigem}
            </span>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-zinc-800 text-zinc-400">
              {pedido.tipo_atendimento}
            </span>
          </div>
          {pedido.identificador && (
            <p className="text-xs text-zinc-400 mt-0.5 truncate">{pedido.identificador}</p>
          )}
        </div>

        <TempoEsperaTimer criadoEm={pedido.criado_em} />
      </div>

      {/* Item e Quantidade em Destaque */}
      <div className="space-y-1.5 flex-1">
        <div className="flex items-baseline gap-2.5">
          <span className="text-2xl font-black text-amber-400 tabular-nums">
            {pedido.quantidade}x
          </span>
          <span className="text-lg font-bold text-zinc-100 leading-snug">
            {pedido.nome_item}
          </span>
        </div>

        {/* Observações em Âmbar com alto contraste */}
        {pedido.observacao && (
          <div className="p-2.5 bg-amber-950/40 border border-amber-800/80 rounded-xl text-xs font-semibold text-amber-200 mt-1">
            <span className="text-amber-400 font-bold uppercase text-[10px] tracking-wider block mb-0.5">
              Observação:
            </span>
            {pedido.observacao}
          </div>
        )}
      </div>

      {/* Ações de 1 Toque (KDS Touch) */}
      <div className="pt-2">
        {pedido.status === 'pendente' && (
          <Button
            variant="primary"
            className="w-full min-h-[48px] bg-amber-600 hover:bg-amber-700 border-amber-600 text-white font-bold text-sm shadow-md"
            isLoading={atualizando}
            onClick={() => handleAvançar('em_preparo')}
          >
            <Flame size={18} className="mr-2" strokeWidth={2} />
            Iniciar Preparo
          </Button>
        )}

        {pedido.status === 'em_preparo' && (
          <Button
            variant="primary"
            className="w-full min-h-[48px] bg-emerald-600 hover:bg-emerald-700 border-emerald-600 text-white font-bold text-sm shadow-md"
            isLoading={atualizando}
            onClick={() => handleAvançar('pronto')}
          >
            <CheckCircle size={18} className="mr-2" strokeWidth={2} />
            Marcar como Pronto!
          </Button>
        )}

        {pedido.status === 'pronto' && (
          <Button
            variant="secondary"
            className="w-full min-h-[48px] border-emerald-600/60 bg-emerald-950/20 text-emerald-300 font-bold text-sm hover:bg-emerald-900/30"
            isLoading={atualizando}
            onClick={() => handleAvançar('entregue')}
          >
            <BellRing size={18} className="mr-2" strokeWidth={2} />
            Pronto (Aguardando Entrega)
          </Button>
        )}
      </div>
    </div>
  )
}
