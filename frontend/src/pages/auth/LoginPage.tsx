import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UtensilsCrossed, LogIn, ArrowRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui'

export function LoginPage() {
  const { loginDono, isLoading } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErro(null)

    if (!email || !senha) {
      setErro('Preencha todos os campos.')
      return
    }

    try {
      await loginDono({ email, senha })
      navigate('/admin')
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'Credenciais inválidas.')
      } else {
        setErro('Erro ao realizar login. Tente novamente.')
      }
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
            Acesso administrativo para donos e gestores
          </p>
        </div>

        {/* Card de Login */}
        <Card>
          <CardHeader>
            <CardTitle>Entrar no Painel</CardTitle>
            <CardDescription>
              Informe suas credenciais para gerenciar seus restaurantes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {erro && (
                <div className="p-3 text-xs rounded-md bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-400">
                  {erro}
                </div>
              )}

              <Input
                label="E-mail"
                id="email"
                type="email"
                autoComplete="username"
                spellCheck={false}
                placeholder="seu@restaurante.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Senha"
                id="senha"
                type="password"
                autoComplete="current-password"
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
                leftIcon={<LogIn className="w-4 h-4" />}
              >
                Entrar no Sistema
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
                  to="/acesso/demo"
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
