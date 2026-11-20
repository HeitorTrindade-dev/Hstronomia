import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { UtensilsCrossed, LogIn, ArrowRight, Clock, AlertCircle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui'

const loginSchema = z.object({
  email: z.string().min(1, 'Informe o e-mail').email('E-mail em formato inválido'),
  senha: z.string().min(1, 'Informe a senha'),
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginDono() {
  const { loginDono, isLoading } = useAuth()
  const navigate = useNavigate()

  const [erro, setErro] = useState<string | null>(null)
  const [retryAfter, setRetryAfter] = useState<number | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      senha: '',
    },
  })

  // Timer decrescente caso ocorra HTTP 429 (Rate Limit)
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

  const onSubmit = async (data: LoginFormData) => {
    setErro(null)
    setRetryAfter(null)

    try {
      await loginDono(data)
      navigate('/admin')
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
          setErro('Muitas tentativas incorretas. Acesso temporariamente bloqueado.')
          return
        }

        setErro(axiosErr.response?.data?.detail || 'Credenciais inválidas.')
      } else {
        setErro('Erro ao realizar login. Verifique sua conexão e tente novamente.')
      }
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
            Acesso administrativo para donos e gestores
          </p>
        </div>

        {/* Card de Autenticação */}
        <Card>
          <CardHeader>
            <CardTitle>Entrar no Painel</CardTitle>
            <CardDescription>
              Informe suas credenciais para gerenciar seus restaurantes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Alerta de Erro Normal */}
              {erro && !retryAfter && (
                <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{erro}</span>
                </div>
              )}

              {/* Alerta de Rate Limit 429 com contagem regressiva */}
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
                label="E-mail"
                id="email"
                type="email"
                autoComplete="username"
                spellCheck={false}
                placeholder="seu@restaurante.com"
                error={errors.email?.message}
                disabled={retryAfter !== null}
                {...register('email')}
              />

              <Input
                label="Senha"
                id="senha"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                error={errors.senha?.message}
                disabled={retryAfter !== null}
                {...register('senha')}
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                isLoading={isLoading}
                disabled={retryAfter !== null}
                leftIcon={<LogIn className="w-4 h-4" />}
              >
                {retryAfter !== null ? `Aguarde ${retryAfter}s` : 'Entrar no Sistema'}
              </Button>
            </form>

            <div className="pt-4 mt-4 border-t border-zinc-100 dark:border-zinc-800 text-center space-y-2">
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Ainda não tem conta?{' '}
                <Link
                  to="/cadastrar"
                  className="font-medium text-red-600 dark:text-red-400 hover:underline"
                >
                  Cadastre-se
                </Link>
              </p>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Acesso de garçom ou cozinha?{' '}
                <Link
                  to="/acesso/cantina-famiglia"
                  className="font-medium text-zinc-700 dark:text-zinc-300 hover:underline inline-flex items-center gap-0.5"
                >
                  Acesso por PIN <ArrowRight className="w-3 h-3" />
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
