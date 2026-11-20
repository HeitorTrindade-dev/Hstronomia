export type StatusItemCozinha = 'pendente' | 'em_preparo' | 'pronto' | 'entregue'
export type StatusFilaCozinha = 'pendente' | 'em_preparo' | 'pronto'

export interface CozinhaPedido {
  id: string
  comanda_id: string
  item_id: string
  nome_item: string
  quantidade: number
  observacao: string | null
  status: StatusItemCozinha
  criado_em: string
  numero_mesa: number | null
  identificador: string | null
  tipo_atendimento: string
}
