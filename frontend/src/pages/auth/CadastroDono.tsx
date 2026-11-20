import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { UtensilsCrossed, UserPlus, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { authService } from '../../services/auth'
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui'

const cadastroSchema = z
  .object({
    nome: z.string().min(2, 'O nome deve ter pelo menos 2 caracteres'),
    email: z.string().min(1, 'Informe o e-mail').email('E-mail em formato inválido'),
    senha: z.string().min(6, 'A senha deve ter no mínimo 6 caracteres').max(72, 'A senha não pode exceder 72 caracteres'),
    confirmacaoSenha: z.string().min(1, 'Confirme a senha informada'),
  })
  .refine((data) => data.senha === data.confirmacaoSenha, {
    message: 'As senhas não coincidem',
    path: ['confirmacaoSenha'],
  })

type CadastroFormData = z.infer<typeof cadastroSchema>

export function CadastroDono() {
  const navigate = useNavigate()

  const [erro, setErro] = useState<string | null>(null)
  const [retryAfter, setRetryAfter] = useState<number | null>(null)
  const [sucesso, setSucesso] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CadastroFormData>({
    resolver: zodResolver(cadastroSchema),
    defaultValues: {
      nome: '',
      email: '',
      senha: '',
      confirmacaoSenha: '',
    },
  })

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

  const onSubmit = async (data: CadastroFormData) => {
    setErro(null)
    setRetryAfter(null)
    setIsLoading(true)

    try {
      await authService.cadastrarDono({
        nome: data.nome,
        email: data.email,
        senha: data.senha,
      })
      setSucesso(true)
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: unknown) {
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
          const segundos = headerRetry ? parseInt(headerRetry, 10) : 60
          setRetryAfter(Number.isNaN(segundos) ? 60 : segundos)
          setErro('Muitas requisições. Aguarde antes de tentar novamente.')
          return
        }

        setErro(axiosErr.response?.data?.detail || 'Erro ao realizar cadastro.')
      } else {
        setErro('Erro ao comunicar com o servidor. Tente novamente.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <div className="w-full max-w-sm space-y-6">
        {/* Marca Hstronomia */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-10 h-10 rounded-md bg-red-50 dark:bg-red-950/40 text-red-600 flex items-center justify-center border border-red-100 dark:border-red-900/50">
            <UtensilsCrossed className="w-5 h-5" strokeWidth={2} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Hstronomia</h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Cadastro de novo gestor ou proprietário
          </p>
        </div>

        {/* Card de Cadastro */}
        <Card>
          <CardHeader>
            <CardTitle>Criar Conta de Dono</CardTitle>
            <CardDescription>
              Cadastre-se para criar e gerenciar restaurantes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sucesso ? (
              <div className="p-4 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center space-y-2">
                <CheckCircle className="w-6 h-6 text-emerald-600 mx-auto" />
                <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                  Conta criada com sucesso!
                </p>
                <p className="text-xs text-emerald-700 dark:text-emerald-400">
                  Redirecionando para a tela de login...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {erro && !retryAfter && (
                  <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{erro}</span>
                  </div>
                )}

                {retryAfter !== null && (
                  <div className="p-3 text-xs rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-800 dark:text-amber-300 space-y-1">
                    <div className="flex items-center gap-1.5 font-medium">
                      <Clock className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
                      <span>Bloqueio temporário por segurança</span>
                    </div>
                    <p>
                      Aguarde <strong className="tabular-nums font-mono">{retryAfter}s</strong> antes de tentar novamente.
                    </p>
                  </div>
                )}

                <Input
                  label="Nome Completo"
                  id="nome"
                  autoComplete="name"
                  placeholder="Seu nome completo"
                  error={errors.nome?.message}
                  disabled={isLoading || retryAfter !== null}
                  {...register('nome')}
                />

                <Input
                  label="E-mail"
                  id="email"
                  type="email"
                  autoComplete="username"
                  spellCheck={false}
                  placeholder="seu@restaurante.com"
                  error={errors.email?.message}
                  disabled={isLoading || retryAfter !== null}
                  {...register('email')}
                />

                <Input
                  label="Senha"
                  id="senha"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Mínimo 6 caracteres"
                  error={errors.senha?.message}
                  disabled={isLoading || retryAfter !== null}
                  {...register('senha')}
                />

                <Input
                  label="Confirmar Senha"
                  id="confirmacaoSenha"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Repita a senha"
                  error={errors.confirmacaoSenha?.message}
                  disabled={isLoading || retryAfter !== null}
                  {...register('confirmacaoSenha')}
                />

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full"
                  isLoading={isLoading}
                  disabled={retryAfter !== null}
                  leftIcon={<UserPlus className="w-4 h-4" />}
                >
                  {retryAfter !== null ? `Aguarde ${retryAfter}s` : 'Finalizar Cadastro'}
                </Button>
              </form>
            )}

            <div className="pt-4 mt-4 border-t border-zinc-100 dark:border-zinc-800 text-center">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Já possui uma conta?{' '}
                <Link
                  to="/login"
                  className="font-medium text-red-600 dark:text-red-400 hover:underline"
                >
                  Fazer login
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
