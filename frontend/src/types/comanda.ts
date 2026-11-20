export type TipoAtendimento = 'mesa' | 'balcao' | 'viagem'
export type StatusComanda = 'aberta' | 'fechada' | 'cancelada'
export type MetodoPagamento = 'pix' | 'dinheiro' | 'cartao_credito' | 'cartao_debito'
export type StatusItemComanda = 'pendente' | 'em_preparo' | 'pronto' | 'entregue' | 'cancelado'

export interface ItemComanda {
  id: string
  comanda_id: string
  item_id: string
  nome_item: string
  quantidade: number
  preco_unitario: number | string
  observacao: string | null
  status: StatusItemComanda
  criado_em: string
}

export interface Comanda {
  id: string
  restaurante_id: string
  numero_mesa: number | null
  identificador: string | null
  tipo_atendimento: TipoAtendimento
  status: StatusComanda
  subtotal: number | string
  taxa_servico: number | string
  desconto: number | string
  valor_total: number | string
  metodo_pagamento: MetodoPagamento | null
  criado_em: string
  fechado_em: string | null
  itens?: ItemComanda[]
}

export interface ComandaPrevia {
  comanda_id: string
  restaurante_id: string
  numero_mesa: number | null
  identificador: string | null
  tipo_atendimento: TipoAtendimento
  status: StatusComanda
  itens: ItemComanda[]
  subtotal: number | string
  incluir_taxa_servico: boolean
  taxa_servico: number | string
  desconto: number | string
  valor_total: number | string
}

export interface ComandaCreateInput {
  numero_mesa?: number | null
  identificador?: string | null
  tipo_atendimento: TipoAtendimento
}

export interface ItemComandaCreateInput {
  item_id: string
  quantidade: number
  observacao?: string | null
}

export interface ItemComandaUpdateInput {
  quantidade?: number
  observacao?: string | null
}

export interface ComandaFecharInput {
  metodo_pagamento: MetodoPagamento
  incluir_taxa_servico: boolean
  desconto: number
}
