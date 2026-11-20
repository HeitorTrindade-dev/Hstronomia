import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Plus,
  Search,
  BookOpen,
  Pencil,
  Power,
  PowerOff,
  RotateCcw,
  Trash2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { cardapioService } from '../../services/cardapio'
import { restauranteService } from '../../services/restaurante'
import { Item, ItemCreateInput } from '../../types/cardapio'
import { Restaurante } from '../../types/restaurante'
import { TopBar } from '../../components/layout/TopBar'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonTableRow,
  EmptyState,
  Modal,
} from '../../components/ui'
import { ItemModal } from '../../components/cardapio/ItemModal'

export function Cardapio() {
  const { user, restaurante: restauranteAtivo, setRestauranteAtivo, logout } = useAuth()

  const [itens, setItens] = useState<Item[]>([])
  const [restaurantes, setRestaurantes] = useState<Restaurante[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [busca, setBusca] = useState('')
  const [incluirInativos, setIncluirInativos] = useState(false)
  const [apenasDisponiveis, setApenasDisponiveis] = useState(false)

  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState<string | null>(null)

  // Modais
  const [isItemModalOpen, setIsItemModalOpen] = useState(false)
  const [itemParaEditar, setItemParaEditar] = useState<Item | null>(null)
  const [itemParaDesativar, setItemParaDesativar] = useState<Item | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  // Carrega restaurantes do dono para troca rápida
  useEffect(() => {
    const buscarRestaurantes = async () => {
      try {
        const lista = await restauranteService.listarMeusRestaurantes()
        setRestaurantes(lista)
      } catch {
        // silencioso
      }
    }
    buscarRestaurantes()
  }, [])

  // Carrega itens do cardápio do restaurante ativo
  const carregarCardapio = useCallback(async () => {
    if (!restauranteAtivo) {
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setErro(null)
    try {
      const lista = await cardapioService.listarItens({
        restaurante_id: restauranteAtivo.id,
        incluir_inativos: incluirInativos,
        apenas_disponiveis: apenasDisponiveis,
      })
      setItens(lista)
    } catch {
      setErro('Erro ao carregar os itens do cardápio.')
    } finally {
      setIsLoading(false)
    }
  }, [restauranteAtivo, incluirInativos, apenasDisponiveis])

  useEffect(() => {
    carregarCardapio()
  }, [carregarCardapio])

  // Filtro de busca local por nome ou descrição
  const itensFiltrados = useMemo(() => {
    if (!busca.trim()) return itens
    const termo = busca.toLowerCase()
    return itens.filter(
      (item) =>
        item.nome.toLowerCase().includes(termo) ||
        (item.descricao && item.descricao.toLowerCase().includes(termo))
    )
  }, [itens, busca])

  // Salvar novo item ou edição
  const handleSalvarItem = async (data: ItemCreateInput) => {
    if (!restauranteAtivo) return
    setIsSaving(true)
    setErro(null)
    setSucesso(null)

    try {
      if (itemParaEditar) {
        await cardapioService.atualizarItem(restauranteAtivo.id, itemParaEditar.id, data)
        setSucesso(`Item "${data.nome}" atualizado com sucesso.`)
      } else {
        await cardapioService.criarItem(restauranteAtivo.id, data)
        setSucesso(`Item "${data.nome}" adicionado ao cardápio com sucesso.`)
      }
      await carregarCardapio()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'Erro ao salvar item.')
      } else {
        setErro('Erro de conexão ao salvar item.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  // Toggle rápido de disponibilidade (mutação otimista)
  const handleToggleDisponibilidade = async (item: Item) => {
    if (!restauranteAtivo) return

    const novoEstado = !item.disponivel
    // Otimista
    setItens((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, disponivel: novoEstado } : i))
    )

    try {
      await cardapioService.alterarDisponibilidade(restauranteAtivo.id, item.id, novoEstado)
    } catch {
      // Reverte em caso de falha
      setItens((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, disponivel: item.disponivel } : i))
      )
      setErro('Não foi possível alterar a disponibilidade do item.')
    }
  }

  // Desativar item (soft delete)
  const handleConfirmarDesativacao = async () => {
    if (!restauranteAtivo || !itemParaDesativar) return
    setIsSaving(true)
    try {
      await cardapioService.desativarItem(restauranteAtivo.id, itemParaDesativar.id)
      setSucesso(`Item "${itemParaDesativar.nome}" desativado do cardápio.`)
      setItemParaDesativar(null)
      await carregarCardapio()
    } catch {
      setErro('Erro ao desativar item.')
    } finally {
      setIsSaving(false)
    }
  }

  // Reativar item
  const handleReativarItem = async (item: Item) => {
    if (!restauranteAtivo) return
    try {
      await cardapioService.reativarItem(restauranteAtivo.id, item.id, true)
      setSucesso(`Item "${item.nome}" reativado no cardápio.`)
      await carregarCardapio()
    } catch {
      setErro('Erro ao reativar item.')
    }
  }

  const formatarMoeda = (valor: number | string) => {
    return Number(valor).toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    })
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col">
      <TopBar
        restaurantName={restauranteAtivo?.nome}
        role="dono"
        userName={user?.nome}
        onLogout={logout}
        restaurantesDisponiveis={restaurantes}
        onSelectRestaurante={(r) =>
          setRestauranteAtivo({ id: r.id, nome: r.nome, slug: r.slug })
        }
      />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Cabeçalho */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Gestão do Cardápio</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Gerencie pratos, preços congelados, disponibilidade e produtos ativos no salão.
            </p>
          </div>

          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => {
              setItemParaEditar(null)
              setIsItemModalOpen(true)
            }}
          >
            Novo Item
          </Button>
        </div>

        {/* Feedback Messages */}
        {sucesso && (
          <div className="p-3 text-xs rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{sucesso}</span>
          </div>
        )}

        {erro && (
          <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{erro}</span>
          </div>
        )}

        {/* Barra de Filtros e Busca */}
        <Card>
          <CardContent className="p-3">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
              <div className="w-full sm:w-72">
                <Input
                  placeholder="Buscar prato por nome ou ingrediente..."
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  leftIcon={<Search className="w-4 h-4" />}
                />
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-zinc-700 dark:text-zinc-300 select-none">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={apenasDisponiveis}
                    onChange={(e) => setApenasDisponiveis(e.target.checked)}
                    className="w-4 h-4 rounded text-red-600 focus:ring-red-500 border-zinc-300 dark:border-zinc-700"
                  />
                  <span>Apenas disponíveis</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={incluirInativos}
                    onChange={(e) => setIncluirInativos(e.target.checked)}
                    className="w-4 h-4 rounded text-red-600 focus:ring-red-500 border-zinc-300 dark:border-zinc-700"
                  />
                  <span>Exibir inativos (desativados)</span>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabela de Itens */}
        <Card className="overflow-hidden">
          <CardHeader className="bg-zinc-50/50 dark:bg-zinc-800/40 p-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-zinc-500" />
                <CardTitle className="text-sm font-semibold">Itens Cadastrados</CardTitle>
              </div>
              <span className="text-xs text-zinc-500 dark:text-zinc-400 tabular-nums">
                {itensFiltrados.length} {itensFiltrados.length === 1 ? 'item' : 'itens'}
              </span>
            </div>
          </CardHeader>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-100/60 dark:bg-zinc-800/60 text-zinc-500 dark:text-zinc-400 uppercase tracking-wider text-[11px] select-none">
                  <th className="py-2.5 px-4 font-semibold">Nome e Descrição</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Preço</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Status</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                {isLoading ? (
                  <>
                    <tr>
                      <td colSpan={4} className="p-0">
                        <SkeletonTableRow columns={4} />
                      </td>
                    </tr>
                    <tr>
                      <td colSpan={4} className="p-0">
                        <SkeletonTableRow columns={4} />
                      </td>
                    </tr>
                    <tr>
                      <td colSpan={4} className="p-0">
                        <SkeletonTableRow columns={4} />
                      </td>
                    </tr>
                    <tr>
                      <td colSpan={4} className="p-0">
                        <SkeletonTableRow columns={4} />
                      </td>
                    </tr>
                  </>
                ) : itensFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center">
                      <EmptyState
                        icon={BookOpen}
                        title={
                          busca
                            ? 'Nenhum item corresponde à busca'
                            : 'Cardápio ainda vazio'
                        }
                        description={
                          busca
                            ? 'Tente pesquisar com outro termo ou limpe os filtros de busca.'
                            : 'Cadastre o primeiro prato ou bebida para o seu restaurante.'
                        }
                        action={
                          !busca
                            ? {
                                label: 'Cadastrar Primeiro Item',
                                onClick: () => {
                                  setItemParaEditar(null)
                                  setIsItemModalOpen(true)
                                },
                                leftIcon: <Plus className="w-4 h-4" />,
                              }
                            : undefined
                        }
                      />
                    </td>
                  </tr>
                ) : (
                  itensFiltrados.map((item) => {
                    const isDesativado = !item.ativo

                    return (
                      <tr
                        key={item.id}
                        className={`hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-colors ${
                          isDesativado ? 'opacity-60 bg-zinc-50/50 dark:bg-zinc-900/50' : ''
                        }`}
                      >
                        <td className="py-3 px-4">
                          <div className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
                            {item.nome}
                          </div>
                          {item.descricao && (
                            <p className="text-zinc-500 dark:text-zinc-400 text-xs line-clamp-1 mt-0.5">
                              {item.descricao}
                            </p>
                          )}
                        </td>

                        <td className="py-3 px-4 text-right font-medium text-zinc-900 dark:text-zinc-100 tabular-nums text-sm">
                          {formatarMoeda(item.preco)}
                        </td>

                        <td className="py-3 px-4 text-center">
                          {isDesativado ? (
                            <Badge variant="zinc" size="sm">
                              Inativo (Desativado)
                            </Badge>
                          ) : item.disponivel ? (
                            <Badge variant="emerald" size="sm" withDot>
                              Disponível
                            </Badge>
                          ) : (
                            <Badge variant="amber" size="sm" withDot>
                              Pausado no Salão
                            </Badge>
                          )}
                        </td>

                        <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
                          {isDesativado ? (
                            <Button
                              variant="secondary"
                              size="sm"
                              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                              onClick={() => handleReativarItem(item)}
                              title="Reativar item no cardápio"
                            >
                              Reativar
                            </Button>
                          ) : (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleToggleDisponibilidade(item)}
                                title={
                                  item.disponivel
                                    ? 'Pausar disponibilidade temporariamente'
                                    : 'Tornar disponível para pedidos'
                                }
                                className={
                                  item.disponivel
                                    ? 'text-amber-600 hover:text-amber-700'
                                    : 'text-emerald-600 hover:text-emerald-700'
                                }
                              >
                                {item.disponivel ? (
                                  <PowerOff className="w-3.5 h-3.5" />
                                ) : (
                                  <Power className="w-3.5 h-3.5" />
                                )}
                              </Button>

                              <Button
                                variant="ghost"
                                size="sm"
                                leftIcon={<Pencil className="w-3.5 h-3.5" />}
                                onClick={() => {
                                  setItemParaEditar(item)
                                  setIsItemModalOpen(true)
                                }}
                                title="Editar nome, descrição ou preço"
                              >
                                Editar
                              </Button>

                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setItemParaDesativar(item)}
                                className="text-zinc-400 hover:text-red-600"
                                title="Desativar item (soft delete)"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </>
                          )}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </main>

      {/* Modal de Criar / Editar Item */}
      <ItemModal
        isOpen={isItemModalOpen}
        onClose={() => {
          setIsItemModalOpen(false)
          setItemParaEditar(null)
        }}
        onSave={handleSalvarItem}
        itemParaEditar={itemParaEditar}
        isLoading={isSaving}
      />

      {/* Modal de Confirmação de Desativação */}
      {itemParaDesativar && (
        <Modal
          isOpen={Boolean(itemParaDesativar)}
          onClose={() => setItemParaDesativar(null)}
          title="Desativar Item do Cardápio"
          description={`Tem certeza que deseja desativar o item "${itemParaDesativar.nome}"?`}
          size="sm"
        >
          <div className="space-y-4">
            <p className="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
              O item não será excluído fisicamente para preservar o histórico financeiro de vendas já realizadas, mas deixará de aparecer para novas comandas e garçons.
            </p>

            <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setItemParaDesativar(null)}
                disabled={isSaving}
              >
                Cancelar
              </Button>
              <Button
                variant="danger"
                size="sm"
                isLoading={isSaving}
                onClick={handleConfirmarDesativacao}
              >
                Confirmar Desativação
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
