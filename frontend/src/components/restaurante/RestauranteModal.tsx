import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Check, Plus } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { Restaurante, RestauranteCreateInput, RestauranteUpdateInput } from '../../types/restaurante'

const restauranteSchema = z
  .object({
    nome: z.string().min(2, 'O nome deve ter no mínimo 2 caracteres').max(120),
    slug: z
      .string()
      .min(2, 'O slug deve ter no mínimo 2 caracteres')
      .max(100)
      .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Apenas letras minúsculas, números e hífens (ex: minha-pizzaria)'),
    codigo_garcom: z.string().min(4, 'O PIN deve ter entre 4 e 20 dígitos').max(20).optional(),
    codigo_cozinha: z.string().min(4, 'O PIN deve ter entre 4 e 20 dígitos').max(20).optional(),
  })
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

type RestauranteFormData = z.infer<typeof restauranteSchema>

export interface RestauranteModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: RestauranteCreateInput | RestauranteUpdateInput) => Promise<void>
  restauranteParaEditar?: Restaurante | null
  isLoading?: boolean
}

export function RestauranteModal({
  isOpen,
  onClose,
  onSave,
  restauranteParaEditar,
  isLoading = false,
}: RestauranteModalProps) {
  const isEditing = Boolean(restauranteParaEditar)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RestauranteFormData>({
    resolver: zodResolver(restauranteSchema),
    defaultValues: {
      nome: '',
      slug: '',
      codigo_garcom: '',
      codigo_cozinha: '',
    },
  })

  useEffect(() => {
    if (restauranteParaEditar) {
      reset({
        nome: restauranteParaEditar.nome,
        slug: restauranteParaEditar.slug,
        codigo_garcom: '',
        codigo_cozinha: '',
      })
    } else {
      reset({
        nome: '',
        slug: '',
        codigo_garcom: '',
        codigo_cozinha: '',
      })
    }
  }, [restauranteParaEditar, reset, isOpen])

  const onSubmit = async (data: RestauranteFormData) => {
    if (isEditing) {
      await onSave({
        nome: data.nome,
        slug: data.slug,
      })
    } else {
      await onSave({
        nome: data.nome,
        slug: data.slug,
        codigo_garcom: data.codigo_garcom || '',
        codigo_cozinha: data.codigo_cozinha || '',
      })
    }
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Restaurante' : 'Novo Restaurante'}
      description={
        isEditing
          ? 'Atualize o nome e o slug de identificação do estabelecimento.'
          : 'Cadastre um novo restaurante com seus PINs operacionais iniciais.'
      }
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Nome do Estabelecimento"
          id="restaurante-nome"
          placeholder="Ex: Cantina Famiglia Bella"
          error={errors.nome?.message}
          autoFocus
          {...register('nome')}
        />

        <Input
          label="Slug de Acesso Operacional (URL)"
          id="restaurante-slug"
          placeholder="ex: cantina-famiglia"
          hint="Será utilizado pelos garçons para acessar /acesso/seu-slug"
          error={errors.slug?.message}
          {...register('slug')}
        />

        {!isEditing && (
          <div className="grid grid-cols-2 gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800">
            <Input
              label="PIN do Garçom (4 a 20 dígitos)"
              id="restaurante-pin-garcom"
              type="password"
              inputMode="numeric"
              placeholder="••••"
              error={errors.codigo_garcom?.message}
              {...register('codigo_garcom')}
            />

            <Input
              label="PIN da Cozinha (4 a 20 dígitos)"
              id="restaurante-pin-cozinha"
              type="password"
              inputMode="numeric"
              placeholder="••••"
              error={errors.codigo_cozinha?.message}
              {...register('codigo_cozinha')}
            />
          </div>
        )}

        <div className="flex justify-end gap-2 pt-3 border-t border-zinc-100 dark:border-zinc-800">
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isLoading}
            leftIcon={isEditing ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          >
            {isEditing ? 'Salvar Dados' : 'Criar Restaurante'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
