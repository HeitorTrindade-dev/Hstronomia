import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { KeyRound, ShieldAlert } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { RestaurantePinsUpdateInput } from '../../types/restaurante'

const pinsSchema = z
  .object({
    codigo_garcom: z.string().min(4, 'O PIN deve ter entre 4 e 20 dígitos').max(20).optional().or(z.literal('')),
    codigo_cozinha: z.string().min(4, 'O PIN deve ter entre 4 e 20 dígitos').max(20).optional().or(z.literal('')),
  })
  .refine(
    (data) => {
      return Boolean(data.codigo_garcom || data.codigo_cozinha)
    },
    {
      message: 'Informe ao menos um novo PIN para atualização',
      path: ['codigo_garcom'],
    }
  )
  .refine(
    (data) => {
      if (data.codigo_garcom && data.codigo_cozinha) {
        return data.codigo_garcom !== data.codigo_cozinha
      }
      return true
    },
    {
      message: 'O PIN do garçom e o PIN da cozinha devem ser diferentes',
      path: ['codigo_cozinha'],
    }
  )

type PinsFormData = z.infer<typeof pinsSchema>

export interface PinsModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: RestaurantePinsUpdateInput) => Promise<void>
  restauranteNome: string
  isLoading?: boolean
}

export function PinsModal({
  isOpen,
  onClose,
  onSave,
  restauranteNome,
  isLoading = false,
}: PinsModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PinsFormData>({
    resolver: zodResolver(pinsSchema),
    defaultValues: {
      codigo_garcom: '',
      codigo_cozinha: '',
    },
  })

  const onSubmit = async (data: PinsFormData) => {
    const payload: RestaurantePinsUpdateInput = {}
    if (data.codigo_garcom) payload.codigo_garcom = data.codigo_garcom
    if (data.codigo_cozinha) payload.codigo_cozinha = data.codigo_cozinha

    await onSave(payload)
    reset()
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Rotacionar PINs Operacionais"
      description={`Atualize os códigos de acesso das equipes para o estabelecimento ${restauranteNome}.`}
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="p-3 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
          <span>
            Ao alterar os PINs, qualquer sessão ativa de garçons ou cozinheiros precisará ser reiniciada com o novo código.
          </span>
        </div>

        <Input
          label="Novo PIN do Garçom (Opcional - 4 a 20 dígitos)"
          id="novo-pin-garcom"
          type="password"
          inputMode="numeric"
          placeholder="Deixe em branco para manter o atual"
          error={errors.codigo_garcom?.message}
          {...register('codigo_garcom')}
        />

        <Input
          label="Novo PIN da Cozinha (Opcional - 4 a 20 dígitos)"
          id="novo-pin-cozinha"
          type="password"
          inputMode="numeric"
          placeholder="Deixe em branco para manter o atual"
          error={errors.codigo_cozinha?.message}
          {...register('codigo_cozinha')}
        />

        <div className="flex justify-end gap-2 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            leftIcon={<KeyRound className="w-4 h-4" />}
          >
            Confirmar Rotação
          </Button>
        </div>
      </form>
    </Modal>
  )
}
