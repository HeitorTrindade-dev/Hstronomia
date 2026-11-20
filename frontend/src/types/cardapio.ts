export interface Item {
  id: string
  restaurante_id: string
  nome: string
  descricao: string | null
  preco: number | string
  disponivel: boolean
  ativo: boolean
  criado_em: string
}

export interface ItemCreateInput {
  nome: string
  descricao?: string | null
  preco: number
  disponivel?: boolean
}

export interface ItemUpdateInput {
  nome?: string
  descricao?: string | null
  preco?: number
  disponivel?: boolean
}
