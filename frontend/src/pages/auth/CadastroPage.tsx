import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UtensilsCrossed, UserPlus, CheckCircle } from 'lucide-react'
import { authService } from '../../services/auth'
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui'

export function CadastroPage() {
  const navigate = useNavigate()

  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [sucesso, setSucesso] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErro(null)

    if (!nome || !email || !senha) {
      setErro('Preencha todos os campos.')
      return
    }

    setIsLoading(true)
    try {
      await authService.cadastrarDono({ nome, email, senha })
      setSucesso(true)
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'Erro ao realizar cadastro.')
      } else {
        setErro('Erro ao comunicar com o servidor.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100">
      <div className="w-full max-w-sm space-y-6">
        {/* Marca */}
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
                <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                  Conta criada com sucesso!
                </p>
                <p className="text-xs text-emerald-700 dark:text-emerald-400">
                  Redirecionando para a tela de login...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {erro && (
                  <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400">
                    {erro}
                  </div>
                )}

                <Input
                  label="Nome Completo"
                  id="nome"
                  autoComplete="name"
                  placeholder="Seu nome"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  required
                />

                <Input
                  label="E-mail"
                  id="email"
                  type="email"
                  autoComplete="username"
                  spellCheck={false}
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />

                <Input
                  label="Senha (mínimo 6 caracteres)"
                  id="senha"
                  type="password"
                  autoComplete="new-password"
                  placeholder="••••••••"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  required
                />

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full"
                  isLoading={isLoading}
                  leftIcon={<UserPlus className="w-4 h-4" />}
                >
                  Finalizar Cadastro
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
