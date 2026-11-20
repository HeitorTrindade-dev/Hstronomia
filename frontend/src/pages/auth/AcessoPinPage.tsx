import React, { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { UtensilsCrossed, KeyRound, ArrowLeft } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui'

export function AcessoPinPage() {
  const { slug } = useParams<{ slug: string }>()
  const { loginOperacional, isLoading } = useAuth()
  const navigate = useNavigate()

  const [restaurantSlug, setRestaurantSlug] = useState(slug || '')
  const [pin, setPin] = useState('')
  const [erro, setErro] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErro(null)

    if (!restaurantSlug || !pin) {
      setErro('Informe o identificador do restaurante e o PIN.')
      return
    }

    try {
      await loginOperacional({ slug: restaurantSlug, pin })
      // O backend retorna role garcom ou cozinha, o contexto atualiza
      const storedRole = localStorage.getItem('@hstronomia:role')
      if (storedRole === 'cozinha') {
        navigate('/cozinha')
      } else {
        navigate('/garcom')
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setErro(axiosErr.response?.data?.detail || 'PIN ou restaurante inválido.')
      } else {
        setErro('Erro ao validar PIN. Tente novamente.')
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
            Terminal Operacional (Garçom / Cozinha)
          </p>
        </div>

        {/* Card de Acesso por PIN */}
        <Card>
          <CardHeader>
            <CardTitle>Acesso por PIN</CardTitle>
            <CardDescription>
              Digite o identificador do restaurante e o PIN numérico atribuído.
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
                label="Slug do Restaurante"
                id="slug"
                placeholder="ex: cantina-famiglia"
                value={restaurantSlug}
                onChange={(e) => setRestaurantSlug(e.target.value.toLowerCase().trim())}
                required
              />

              <Input
                label="PIN de Acesso (numérico)"
                id="pin"
                type="password"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={20}
                placeholder="••••"
                value={pin}
                onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                required
              />

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                isLoading={isLoading}
                leftIcon={<KeyRound className="w-4 h-4" />}
              >
                Acessar Terminal
              </Button>
            </form>

            <div className="pt-4 mt-4 border-t border-zinc-100 dark:border-zinc-800 text-center">
              <Link
                to="/login"
                className="text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Voltar para login do dono
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
