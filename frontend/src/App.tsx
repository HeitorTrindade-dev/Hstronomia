import { UtensilsCrossed } from 'lucide-react'

export default function App() {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center space-y-4">
        <div className="w-16 h-16 bg-amber-100 text-amber-700 rounded-2xl flex items-center justify-center mx-auto">
          <UtensilsCrossed className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Hstronomia</h1>
          <p className="text-sm text-slate-500 mt-1">
            Sistema de Gestão Operacional e Financeira para Restaurantes
          </p>
        </div>
        <div className="pt-4 border-t border-slate-100 text-xs text-slate-400">
          API Conectada: <code className="text-slate-600 font-mono">{apiUrl}</code>
        </div>
      </div>
    </main>
  )
}
