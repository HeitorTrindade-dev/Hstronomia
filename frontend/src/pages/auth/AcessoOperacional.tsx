import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { UtensilsCrossed, ArrowLeft, Clock, AlertCircle, Store, Users, Flame } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { restauranteService } from '../../services/restaurante'
import { RestaurantePublico } from '../../types/restaurante'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Skeleton } from '../../components/ui'
import { PinKeypad } from '../../components/auth/PinKeypad'

export function AcessoOperacional() {
  const { slug } = useParams<{ slug: string }>()
  const { loginOperacional, isLoading: isAuthLoading } = useAuth()
  const navigate = useNavigate()

  const [restaurante, setRestaurante] = useState<RestaurantePublico | null>(null)
  const [carregandoRestaurante, setCarregandoRestaurante] = useState(true)
  const [erroRestaurante, setErroRestaurante] = useState<string | null>(null)

  const [pin, setPin] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [retryAfter, setRetryAfter] = useState<number | null>(null)
  const [funcaoDesejada, setFuncaoDesejada] = useState<'garcom' | 'cozinha'>('garcom')

  // Carrega os dados públicos do restaurante
  useEffect(() => {
    if (!slug) {
      setErroRestaurante('Identificador do restaurante não informado.')
      setCarregandoRestaurante(false)
      return
    }

    const buscarRestaurante = async () => {
      setCarregandoRestaurante(true)
      setErroRestaurante(null)
      try {
        const dados = await restauranteService.obterPorSlug(slug)
        setRestaurante(dados)
      } catch {
        setErroRestaurante('Restaurante não encontrado ou inativo.')
      } finally {
        setCarregandoRestaurante(false)
      }
    }

    buscarRestaurante()
  }, [slug])

  // Timer para 429
  useEffect(() => {
    if (retryAfter === null || retryAfter <= 0) return

    const timer = setInterval(() => {
      setRetryAfter((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(timer)
          setErro(null)
          return null
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [retryAfter])

  const handleSubmeterPin = useCallback(async () => {
    if (!slug) return
    if (pin.length < 4) {
      setErro('Digite o PIN de pelo menos 4 dígitos.')
      return
    }

    setErro(null)
    setRetryAfter(null)

    try {
      await loginOperacional({ slug, pin })
      const storedRole = localStorage.getItem('@hstronomia:role')
      if (storedRole === 'cozinha') {
        navigate('/cozinha')
      } else {
        navigate('/garcom')
      }
    } catch (err: unknown) {
      setPin('') // Limpa o PIN em caso de falha
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as {
          response?: {
            status?: number
            headers?: Record<string, string>
            data?: { detail?: string }
          }
        }

        if (axiosErr.response?.status === 429) {
          const headerRetry = axiosErr.response.headers?.['retry-after']
          const segundos = headerRetry ? parseInt(headerRetry, 10) : 300
          setRetryAfter(Number.isNaN(segundos) ? 300 : segundos)
          setErro('Muitas tentativas incorretas. Terminal bloqueado temporariamente.')
          return
        }

        setErro(axiosErr.response?.data?.detail || 'PIN incorreto para este restaurante.')
      } else {
        setErro('Erro de conexão. Tente novamente.')
      }
    }
  }, [slug, pin, loginOperacional, navigate])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <div className="w-full max-w-sm space-y-5">
        {/* Marca */}
        <div className="flex flex-col items-center text-center space-y-1">
          <div className="w-10 h-10 rounded-md bg-red-50 dark:bg-red-950/40 text-red-600 flex items-center justify-center border border-red-100 dark:border-red-900/50">
            <UtensilsCrossed className="w-5 h-5" strokeWidth={2} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Hstronomia</h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Terminal Operacional por PIN
          </p>
        </div>

        {/* Card Principal */}
        <Card>
          <CardHeader>
            {carregandoRestaurante ? (
              <div className="space-y-2">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ) : erroRestaurante ? (
              <div>
                <CardTitle className="text-red-600 dark:text-red-400">Restaurante Não Encontrado</CardTitle>
                <CardDescription>{erroRestaurante}</CardDescription>
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-2">
                  <Store className="w-4 h-4 text-zinc-500" />
                  <CardTitle>{restaurante?.nome}</CardTitle>
                </div>
                <CardDescription>
                  Slug: <span className="font-mono text-zinc-700 dark:text-zinc-300">{restaurante?.slug}</span>
                </CardDescription>
              </div>
            )}
          </CardHeader>

          <CardContent className="space-y-4">
            {carregandoRestaurante ? (
              <div className="space-y-4 py-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-48 w-full" />
              </div>
            ) : erroRestaurante ? (
              <div className="text-center py-4 space-y-3">
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Verifique o endereço digitado ou consulte o administrador do restaurante.
                </p>
                <Link to="/login" className="inline-block text-xs text-red-600 dark:text-red-400 hover:underline">
                  Voltar para login do Dono
                </Link>
              </div>
            ) : (
              <>
                {/* Seletor visual da Função Pretendida */}
                <div className="space-y-1.5">
                  <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">
                    Função de Acesso:
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setFuncaoDesejada('garcom')}
                      className={`p-2 rounded-md border text-xs font-medium flex items-center justify-center gap-1.5 transition-colors ${
                        funcaoDesejada === 'garcom'
                          ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 ring-1 ring-sky-500'
                          : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                      }`}
                    >
                      <Users className="w-3.5 h-3.5" />
                      <span>Garçom (Salão)</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setFuncaoDesejada('cozinha')}
                      className={`p-2 rounded-md border text-xs font-medium flex items-center justify-center gap-1.5 transition-colors ${
                        funcaoDesejada === 'cozinha'
                          ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 ring-1 ring-amber-500'
                          : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                      }`}
                    >
                      <Flame className="w-3.5 h-3.5" />
                      <span>Cozinha (KDS)</span>
                    </button>
                  </div>
                </div>

                {/* Alerta de Erro */}
                {erro && !retryAfter && (
                  <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{erro}</span>
                  </div>
                )}

                {/* Alerta de Rate Limit 429 */}
                {retryAfter !== null && (
                  <div className="p-3 text-xs rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 space-y-1">
                    <div className="flex items-center gap-1.5 font-medium">
                      <Clock className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
                      <span>Bloqueio temporário do terminal</span>
                    </div>
                    <p>
                      Muitas tentativas incorretas. Aguarde <strong className="tabular-nums font-mono">{retryAfter}s</strong>.
                    </p>
                  </div>
                )}

                {/* Teclado Virtual Numérico Touch */}
                <div className="pt-1">
                  <div className="text-center mb-1">
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      Digite o PIN numérico atribuído:
                    </span>
                  </div>
                  <PinKeypad
                    pin={pin}
                    onChange={setPin}
                    onSubmit={handleSubmeterPin}
                    disabled={retryAfter !== null}
                    isLoading={isAuthLoading}
                    maxLength={20}
                  />
                </div>
              </>
            )}

            <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800 text-center">
              <Link
                to="/login"
                className="text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Acesso administrativo (Dono)
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
