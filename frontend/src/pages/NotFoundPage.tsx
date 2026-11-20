import { Link } from 'react-router-dom'
import { AlertCircle, ArrowLeft } from 'lucide-react'
import { Button } from '../components/ui'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 text-center">
      <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-950/40 text-red-600 flex items-center justify-center mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h1 className="text-xl font-bold tracking-tight">Página Não Encontrada</h1>
      <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm">
        O endereço acessado não existe ou você não possui permissão para visualizá-lo.
      </p>
      <div className="mt-6">
        <Link to="/">
          <Button variant="secondary" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
            Voltar ao Início
          </Button>
        </Link>
      </div>
    </div>
  )
}
