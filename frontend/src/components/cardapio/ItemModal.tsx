import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Check, Plus } from 'lucide-react'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { Item, ItemCreateInput } from '../../types/cardapio'

const itemSchema = z.object({
  nome: z.string().min(2, 'O nome deve ter no mínimo 2 caracteres').max(120),
  descricao: z.string().max(1000).optional().nullable(),
  preco: z.number().gt(0, 'O preço deve ser maior que R$ 0,00'),
  disponivel: z.boolean(),
})

type ItemFormData = z.infer<typeof itemSchema>

export interface ItemModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: ItemCreateInput) => Promise<void>
  itemParaEditar?: Item | null
  isLoading?: boolean
}

export function ItemModal({
  isOpen,
  onClose,
  onSave,
  itemParaEditar,
  isLoading = false,
}: ItemModalProps) {
  const isEditing = Boolean(itemParaEditar)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ItemFormData>({
    resolver: zodResolver(itemSchema),
    defaultValues: {
      nome: '',
      descricao: '',
      preco: 0,
      disponivel: true,
    },
  })

  useEffect(() => {
    if (itemParaEditar) {
      reset({
        nome: itemParaEditar.nome,
        descricao: itemParaEditar.descricao || '',
        preco: Number(itemParaEditar.preco),
        disponivel: itemParaEditar.disponivel,
      })
    } else {
      reset({
        nome: '',
        descricao: '',
        preco: 0,
        disponivel: true,
      })
    }
  }, [itemParaEditar, reset, isOpen])

  const onSubmit = async (data: ItemFormData) => {
    await onSave({
      nome: data.nome,
      descricao: data.descricao || null,
      preco: data.preco,
      disponivel: data.disponivel,
    })
    onClose()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Editar Item do Cardápio' : 'Cadastrar Novo Item'}
      description={
        isEditing
          ? 'Atualize os dados e preço do item selecionado.'
          : 'Adicione um novo produto ao cardápio do seu restaurante.'
      }
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Nome do Item"
          id="item-nome"
          placeholder="Ex: Pizza Margherita Individual"
          error={errors.nome?.message}
          autoFocus
          {...register('nome')}
        />

        <div className="w-full space-y-1">
          <label htmlFor="item-descricao" className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
            Descrição (Opcional)
          </label>
          <textarea
            id="item-descricao"
            rows={3}
            placeholder="Ingredientes, porção ou detalhes de preparo..."
            className="w-full rounded-md text-sm border p-2.5 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 border-zinc-300 dark:border-zinc-700 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-600 transition-colors resize-none"
            {...register('descricao')}
          />
          {errors.descricao?.message && (
            <p className="text-xs text-red-600 dark:text-red-400">{errors.descricao.message}</p>
          )}
        </div>

        <Input
          label="Preço Unitário (R$)"
          id="item-preco"
          type="number"
          step="0.01"
          placeholder="0.00"
          error={errors.preco?.message}
          {...register('preco', { valueAsNumber: true })}
        />

        <div className="flex items-center gap-2 pt-1">
          <input
            id="item-disponivel"
            type="checkbox"
            className="w-4 h-4 rounded text-red-600 focus:ring-red-500 border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900"
            {...register('disponivel')}
          />
          <label htmlFor="item-disponivel" className="text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none">
            Item disponível para pedidos no salão
          </label>
        </div>

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
            {isEditing ? 'Salvar Alterações' : 'Adicionar ao Cardápio'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
