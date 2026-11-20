import React, { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { comandaService } from '../../services/comanda'
import { useAuth } from '../../contexts/AuthContext'

interface CancelarComandaModalProps {
  isOpen: boolean
  onClose: () => void
  comandaId: string
  identificadorTitulo?: string
  onComandaCancelada: () => void
}

export const CancelarComandaModal: React.FC<CancelarComandaModalProps> = ({
  isOpen,
  onClose,
  comandaId,
  identificadorTitulo,
  onComandaCancelada,
}) => {
  const { restauranteAtivo } = useAuth()
  const [cancelando, setCancelando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const handleConfirmar = async () => {
    try {
      setCancelando(true)
      setErro(null)
      await comandaService.cancelarComanda(comandaId, restauranteAtivo?.id)
      onComandaCancelada()
      onClose()
    } catch {
      setErro('Erro ao cancelar a comanda. Verifique se a comanda já foi encerrada.')
    } finally {
      setCancelando(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Cancelar Comanda"
    >
      <div className="space-y-4">
        {erro && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {erro}
          </div>
        )}

        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
          <AlertTriangle className="text-red-600 shrink-0 mt-0.5" size={20} strokeWidth={2} />
          <div className="text-sm text-red-900 space-y-1">
            <p className="font-semibold">
              Tem certeza que deseja cancelar {identificadorTitulo || 'esta comanda'}?
            </p>
            <p className="text-red-700 text-xs">
              Esta ação desocupará a mesa e cancelará todos os itens associados que não foram entregues.
            </p>
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            variant="secondary"
            className="flex-1 min-h-[44px]"
            onClick={onClose}
            disabled={cancelando}
          >
            Voltar
          </Button>
          <Button
            variant="danger"
            className="flex-1 min-h-[44px]"
            isLoading={cancelando}
            onClick={handleConfirmar}
          >
            Confirmar Cancelamento
          </Button>
        </div>
      </div>
    </Modal>
  )
}
