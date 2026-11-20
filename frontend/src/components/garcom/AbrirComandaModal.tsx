import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Users, Utensils, ShoppingBag } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { ComandaCreateInput, TipoAtendimento } from '../../types/comanda'

const abrirComandaSchema = z
  .object({
    tipo_atendimento: z.enum(['mesa', 'balcao', 'viagem']),
    numero_mesa: z.number().nullable().optional(),
    identificador: z.string().optional().nullable(),
  })
  .refine(
    (data) => {
      if (data.tipo_atendimento === 'mesa') {
        return typeof data.numero_mesa === 'number' && data.numero_mesa > 0
      }
      return Boolean(data.identificador && data.identificador.trim().length > 0)
    },
    {
      message: 'Informe o número da mesa ou o identificador do cliente',
      path: ['numero_mesa'],
    }
  )

type AbrirComandaFormData = {
  tipo_atendimento: TipoAtendimento
  numero_mesa?: number | null
  identificador?: string | null
}

export interface AbrirComandaModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: ComandaCreateInput) => Promise<void>
  mesaPreSelecionada?: number | null
  isLoading?: boolean
}

export function AbrirComandaModal({
  isOpen,
  onClose,
  onSave,
  mesaPreSelecionada,
  isLoading = false,
}: AbrirComandaModalProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<AbrirComandaFormData>({
    resolver: zodResolver(abrirComandaSchema),
    defaultValues: {
      tipo_atendimento: 'mesa',
      numero_mesa: mesaPreSelecionada ?? 1,
      identificador: '',
    },
  })

  const tipoAtendimento = watch('tipo_atendimento')

  useEffect(() => {
    if (mesaPreSelecionada) {
      setValue('tipo_atendimento', 'mesa')
      setValue('numero_mesa', mesaPreSelecionada)
    } else {
      reset({
        tipo_atendimento: 'mesa',
        numero_mesa: 1,
        identificador: '',
      })
    }
  }, [mesaPreSelecionada, setValue, reset, isOpen])

  const onSubmit = async (data: AbrirComandaFormData) => {
    await onSave({
      tipo_atendimento: data.tipo_atendimento,
      numero_mesa: data.tipo_atendimento === 'mesa' ? Number(data.numero_mesa) : null,
      identificador: data.identificador ? data.identificador.trim() : null,
    })
    reset()
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Abrir Nova Comanda"
      description="Inicie um novo atendimento selecionando o local e identificador."
      size="sm"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Seletor de Tipo de Atendimento */}
        <div className="space-y-1">
          <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
            Local de Atendimento
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setValue('tipo_atendimento', 'mesa')}
              className={`p-2.5 rounded-md border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-colors ${
                tipoAtendimento === 'mesa'
                  ? 'border-red-600 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 ring-1 ring-red-600'
                  : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Mesa</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setValue('tipo_atendimento', 'balcao')
                setValue('numero_mesa', null)
              }}
              className={`p-2.5 rounded-md border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-colors ${
                tipoAtendimento === 'balcao'
                  ? 'border-red-600 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 ring-1 ring-red-600'
                  : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'
              }`}
            >
              <Utensils className="w-4 h-4" />
              <span>Balcão</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setValue('tipo_atendimento', 'viagem')
                setValue('numero_mesa', null)
              }}
              className={`p-2.5 rounded-md border text-xs font-medium flex flex-col items-center justify-center gap-1 transition-colors ${
                tipoAtendimento === 'viagem'
                  ? 'border-red-600 bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 ring-1 ring-red-600'
                  : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'
              }`}
            >
              <ShoppingBag className="w-4 h-4" />
              <span>Viagem</span>
            </button>
          </div>
        </div>

        {tipoAtendimento === 'mesa' ? (
          <Input
            label="Número da Mesa"
            id="abrir-numero-mesa"
            type="number"
            min={1}
            max={9999}
            placeholder="Ex: 12"
            error={errors.numero_mesa?.message}
            autoFocus
            {...register('numero_mesa', { valueAsNumber: true })}
          />
        ) : (
          <Input
            label="Identificador do Cliente / Senha"
            id="abrir-identificador"
            placeholder="Ex: Lucas Balcão 02 ou Senha 45"
            error={errors.identificador?.message}
            autoFocus
            {...register('identificador')}
          />
        )}

        {tipoAtendimento === 'mesa' && (
          <Input
            label="Nome ou Referência (Opcional)"
            id="abrir-cliente"
            placeholder="Ex: Família Silva"
            {...register('identificador')}
          />
        )}

        <div className="flex justify-end gap-2 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Abrir Comanda
          </Button>
        </div>
      </form>
    </Modal>
  )
}
