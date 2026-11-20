export type CategoriaDespesa = 'insumos' | 'contas_fixas' | 'manutencao' | 'outros'

export interface Despesa {
  id: string
  restaurante_id: string
  descricao: string
  categoria: CategoriaDespesa
  valor: number | string
  data_pagamento: string
  criado_em: string
}

export interface DespesaCreateInput {
  descricao: string
  categoria: CategoriaDespesa
  valor: number
  data_pagamento: string
}

export interface DespesaUpdateInput {
  descricao?: string
  categoria?: CategoriaDespesa
  valor?: number
  data_pagamento?: string
}

export interface ResumoFinanceiro {
  restaurante_id: string
  data_inicio: string | null
  data_fim: string | null
  total_vendas: number | string
  total_despesas: number | string
  saldo: number | string
  despesas_por_categoria: Record<string, number | string>
}
