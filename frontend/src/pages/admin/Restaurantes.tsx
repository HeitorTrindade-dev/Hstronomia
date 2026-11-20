import { useState, useEffect, useCallback } from 'react'
import { Plus, Store, KeyRound, Pencil, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { restauranteService } from '../../services/restaurante'
import {
  Restaurante,
  RestauranteCreateInput,
  RestaurantePinsUpdateInput,
  RestauranteUpdateInput,
} from '../../types/restaurante'
import { TopBar } from '../../components/layout/TopBar'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
  SkeletonCard,
  EmptyState,
} from '../../components/ui'
import { RestauranteModal } from '../../components/restaurante/RestauranteModal'
import { PinsModal } from '../../components/restaurante/PinsModal'

export function Restaurantes() {
  const { user, restaurante: restauranteAtivo, setRestauranteAtivo, logout } = useAuth()

  const [restaurantes, setRestaurantes] = useState<Restaurante[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState<string | null>(null)

  // Modais
  const [isRestauranteModalOpen, setIsRestauranteModalOpen] = useState(false)
  const [restauranteParaEditar, setRestauranteParaEditar] = useState<Restaurante | null>(null)
  const [isPinsModalOpen, setIsPinsModalOpen] = useState(false)
  const [restauranteParaPins, setRestauranteParaPins] = useState<Restaurante | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const carregarRestaurantes = useCallback(async () => {
    setIsLoading(true)
    setErro(null)
    try {
      const lista = await restauranteService.listarMeusRestaurantes()
      setRestaurantes(lista)

      // Se não houver restaurante ativo configurado e a lista tiver itens, seleciona o primeiro
      if (!restauranteAtivo && lista.length > 0) {
        setRestauranteAtivo({
          id: lista[0].id,
          nome: lista[0].nome,
          slug: lista[0].slug,
        })
      }
    } catch {
      setErro('Erro ao carregar a lista de estabelecimentos.')
    } finally {
      setIsLoading(false)
    }
  }, [restauranteAtivo, setRestauranteAtivo])

  useEffect(() => {
    carregarRestaurantes()
  }, [carregarRestaurantes])

  const handleSalvarRestaurante = async (data: RestauranteCreateInput | RestauranteUpdateInput) => {
    setIsSaving(true)
    setErro(null)
    setSucesso(null)
    try {
      if (restauranteParaEditar) {
        const atualizado = await restauranteService.atualizarRestaurante(
          restauranteParaEditar.id,
          data as RestauranteUpdateInput
        )
        setSucesso(`Estabelecimento "${atualizado.nome}" atualizado com sucesso.`)
        // Se era o restaurante ativo, atualiza o contexto
        if (restauranteAtivo?.id === atualizado.id) {
          setRestauranteAtivo({
            id: atualizado.id,
            nome: atualizado.nome,
            slug: atualizado.slug,
          })
        }
      } else {
        const criado = await restauranteService.criarRestaurante(data as RestauranteCreateInput)
        setSucesso(`Restaurante "${criado.nome}" criado com sucesso.`)
        setRestauranteAtivo({
          id: criado.id,
          nome: criado.nome,
          slug: criado.slug,
        })
      }
      await carregarRestaurantes()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'Erro ao salvar restaurante.')
      } else {
        setErro('Erro de conexão ao salvar.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  const handleSalvarPins = async (data: RestaurantePinsUpdateInput) => {
    if (!restauranteParaPins) return
    setIsSaving(true)
    setErro(null)
    setSucesso(null)
    try {
      await restauranteService.atualizarPins(restauranteParaPins.id, data)
      setSucesso(`PINs do restaurante "${restauranteParaPins.nome}" rotacionados com sucesso.`)
      await carregarRestaurantes()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'Erro ao rotacionar PINs.')
      } else {
        setErro('Erro de conexão ao rotacionar PINs.')
      }
    } finally {
      setIsSaving(false)
    }
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
        {/* Cabeçalho da Página */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Meus Restaurantes</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Gerencie seus estabelecimentos multi-tenant e credenciais operacionais de PIN.
            </p>
          </div>

          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => {
              setRestauranteParaEditar(null)
              setIsRestauranteModalOpen(true)
            }}
          >
            Novo Restaurante
          </Button>
        </div>

        {/* Mensagens de Feedback */}
        {sucesso && (
          <div className="p-3 text-xs rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{sucesso}</span>
          </div>
        )}

        {erro && (
          <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400">
            {erro}
          </div>
        )}

        {/* Listagem de Restaurantes */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : restaurantes.length === 0 ? (
          <EmptyState
            icon={Store}
            title="Nenhum restaurante cadastrado"
            description="Crie seu primeiro estabelecimento para começar a gerenciar o cardápio, comandas e equipe."
            action={{
              label: 'Cadastrar Restaurante',
              onClick: () => {
                setRestauranteParaEditar(null)
                setIsRestauranteModalOpen(true)
              },
              leftIcon: <Plus className="w-4 h-4" />,
            }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {restaurantes.map((rest) => {
              const isAtivo = restauranteAtivo?.id === rest.id

              return (
                <Card
                  key={rest.id}
                  className={`relative transition-all ${
                    isAtivo
                      ? 'ring-2 ring-red-500/80 border-red-200 dark:border-red-900/50'
                      : 'hover:border-zinc-300 dark:hover:border-zinc-700'
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <CardTitle className="text-base">{rest.nome}</CardTitle>
                        <CardDescription>
                          Slug: <span className="font-mono">{rest.slug}</span>
                        </CardDescription>
                      </div>

                      {isAtivo ? (
                        <Badge variant="emerald" size="sm" withDot>
                          Ativo
                        </Badge>
                      ) : (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setRestauranteAtivo({
                              id: rest.id,
                              nome: rest.nome,
                              slug: rest.slug,
                            })
                          }
                          className="text-xs text-zinc-600 hover:text-zinc-900"
                        >
                          Selecionar
                        </Button>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-3">
                    <div className="p-2.5 rounded-md bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-100 dark:border-zinc-800 text-xs space-y-1">
                      <div className="flex justify-between items-center text-zinc-500 dark:text-zinc-400">
                        <span>Acesso Operacional:</span>
                        <code className="text-zinc-700 dark:text-zinc-300 font-mono">
                          /acesso/{rest.slug}
                        </code>
                      </div>
                      <div className="flex justify-between items-center text-zinc-500 dark:text-zinc-400">
                        <span>Criado em:</span>
                        <span className="tabular-nums">
                          {new Date(rest.criado_em).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800/80">
                      <Button
                        variant="secondary"
                        size="sm"
                        leftIcon={<KeyRound className="w-3.5 h-3.5" />}
                        onClick={() => {
                          setRestauranteParaPins(rest)
                          setIsPinsModalOpen(true)
                        }}
                      >
                        PINs
                      </Button>

                      <Button
                        variant="secondary"
                        size="sm"
                        leftIcon={<Pencil className="w-3.5 h-3.5" />}
                        onClick={() => {
                          setRestauranteParaEditar(rest)
                          setIsRestauranteModalOpen(true)
                        }}
                      >
                        Editar
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </main>

      {/* Modal de Criação / Edição de Restaurante */}
      <RestauranteModal
        isOpen={isRestauranteModalOpen}
        onClose={() => {
          setIsRestauranteModalOpen(false)
          setRestauranteParaEditar(null)
        }}
        onSave={handleSalvarRestaurante}
        restauranteParaEditar={restauranteParaEditar}
        isLoading={isSaving}
      />

      {/* Modal de Rotação de PINs */}
      {restauranteParaPins && (
        <PinsModal
          isOpen={isPinsModalOpen}
          onClose={() => {
            setIsPinsModalOpen(false)
            setRestauranteParaPins(null)
          }}
          onSave={handleSalvarPins}
          restauranteNome={restauranteParaPins.nome}
          isLoading={isSaving}
        />
      )}
    </div>
  )
}
