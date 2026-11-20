import { useState, useEffect } from 'react'
import { Plus, Trash2, Search, CheckCircle, Inbox } from 'lucide-react'
import { TopBar, UserRole } from '../components/layout'
import {
  Button,
  Input,
  Select,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Badge,
  Modal,
  Skeleton,
  SkeletonCard,
  EmptyState,
} from '../components/ui'

export function DesignSystemPage() {
  const [isDarkMode, setIsDarkMode] = useState(false)
  const [role, setRole] = useState<UserRole>('dono')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isButtonLoading, setIsButtonLoading] = useState(false)
  const [searchValue, setSearchValue] = useState('')

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDarkMode])

  const toggleLoading = () => {
    setIsButtonLoading(true)
    setTimeout(() => setIsButtonLoading(false), 2000)
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col transition-colors">
      <TopBar
        restaurantName="Cantina Famiglia Hstronomia"
        role={role}
        userName="Administrador"
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
        onLogout={() => alert('Logout disparado')}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-8">
        <div className="border-b border-zinc-200 dark:border-zinc-800 pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
              Fundação de UI e Design System
            </h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Componentes base atômicos, consistência visual, regras anti-AI-slop e acessibilidade nativa.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500 dark:text-zinc-400">Simular Perfil:</span>
            <div className="inline-flex rounded-md border border-zinc-200 dark:border-zinc-800 p-0.5 bg-white dark:bg-zinc-900">
              <button
                type="button"
                onClick={() => setRole('dono')}
                className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                  role === 'dono'
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                Dono
              </button>
              <button
                type="button"
                onClick={() => setRole('garcom')}
                className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                  role === 'garcom'
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                Garçom
              </button>
              <button
                type="button"
                onClick={() => setRole('cozinha')}
                className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                  role === 'cozinha'
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100'
                    : 'text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                Cozinha
              </button>
            </div>
          </div>
        </div>

        {/* 1. Botões */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
            Botões (Button)
          </h2>
          <Card>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
                  Ação Primária
                </Button>
                <Button variant="secondary">Secundário</Button>
                <Button variant="danger" leftIcon={<Trash2 className="w-4 h-4" />}>
                  Remover Item
                </Button>
                <Button variant="ghost">Ação Ghost</Button>
                <Button
                  variant="primary"
                  isLoading={isButtonLoading}
                  onClick={toggleLoading}
                >
                  {isButtonLoading ? 'Processando...' : 'Testar Loading'}
                </Button>
                <Button variant="primary" disabled>
                  Desabilitado
                </Button>
              </div>

              <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800 flex flex-wrap items-center gap-3">
                <Button variant="secondary" size="sm">
                  Pequeno (sm - h8)
                </Button>
                <Button variant="secondary" size="md">
                  Padrão (md - h9)
                </Button>
                <Button variant="secondary" size="lg">
                  Grande (lg - h10)
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* 2. Formulários (Inputs & Selects) */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
            Controles de Formulário (Input & Select)
          </h2>
          <Card>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Nome do Item"
                  placeholder="Ex: Pizza Margherita"
                  hint="Nome como aparecerá no cardápio"
                />
                <Input
                  label="Pesquisar Cardápio"
                  placeholder="Buscar prato..."
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  leftIcon={<Search className="w-4 h-4" />}
                />
                <Input
                  label="Preço Unitário (R$)"
                  placeholder="0,00"
                  error="Valor inválido informado"
                  defaultValue="-10,00"
                />
                <Select
                  label="Categoria"
                  options={[
                    { value: 'pizzas', label: 'Pizzas Tradicionais' },
                    { value: 'bebidas', label: 'Bebidas & Drinks' },
                    { value: 'sobremesas', label: 'Sobremesas' },
                  ]}
                />
                <Select
                  label="Status da Comanda"
                  options={[
                    { value: 'aberta', label: 'Aberta' },
                    { value: 'fechada', label: 'Fechada' },
                    { value: 'cancelada', label: 'Cancelada' },
                  ]}
                />
                <Input
                  label="Campo Desabilitado"
                  defaultValue="Não editável"
                  disabled
                />
              </div>
            </CardContent>
          </Card>
        </section>

        {/* 3. Badges e Semáforo Operacional */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
            Badges de Status (Semáforo Operacional)
          </h2>
          <Card>
            <CardContent>
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant="emerald" withDot>
                  Pronto / Aberto / Disponível (Emerald)
                </Badge>
                <Badge variant="amber" withDot>
                  Em Preparo / Pendente / Ocupado (Amber)
                </Badge>
                <Badge variant="sky" withDot>
                  Entregue / Info (Sky)
                </Badge>
                <Badge variant="red" withDot>
                  Cancelado / Fechada / Alerta (Red)
                </Badge>
                <Badge variant="zinc">Neutro / Inativo (Zinc)</Badge>
                <Badge variant="emerald" size="sm">
                  SM Pronto
                </Badge>
                <Badge variant="red" size="sm">
                  R$ 145,90
                </Badge>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* 4. Skeletons e Prevenção de CLS */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
            Skeletons (Prevenção de Cumulative Layout Shift)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SkeletonCard />
            <Card>
              <CardHeader>
                <CardTitle>Linhas de Tabela em Carregamento</CardTitle>
                <CardDescription>
                  Geometria espelhada para evitar saltos visuais na renderização de dados assíncronos.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center gap-3">
                  <Skeleton variant="circle" className="w-8 h-8" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton variant="text" className="w-3/4" />
                    <Skeleton variant="text" className="w-1/2" />
                  </div>
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <Skeleton variant="circle" className="w-8 h-8" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton variant="text" className="w-2/3" />
                    <Skeleton variant="text" className="w-1/3" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 5. Empty State e Diálogo Modal */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
              Estado Vazio (EmptyState)
            </h2>
            <EmptyState
              icon={Inbox}
              title="Nenhuma comanda ativa no momento"
              description="Quando novas comandas forem abertas pelos garçons, elas serão listadas nesta área."
              action={{
                label: 'Abrir Nova Comanda',
                onClick: () => setIsModalOpen(true),
                leftIcon: <Plus className="w-4 h-4" />,
              }}
            />
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-semibold tracking-wide uppercase text-zinc-500 dark:text-zinc-400">
              Diálogo Modal Nativo (Modal)
            </h2>
            <Card>
              <CardHeader>
                <CardTitle>Modal com Dialog Nativo</CardTitle>
                <CardDescription>
                  Acessibilidade com foco gerenciado, tecla Esc e suporte a light-dismiss.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                  Clique no botão abaixo para testar a abertura do modal acessível nativo.
                </p>
                <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                  Abrir Modal de Teste
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Abrir Nova Comanda"
        description="Preencha os dados básicos para iniciar o atendimento."
      >
        <div className="space-y-4">
          <Input label="Número da Mesa" placeholder="Ex: Mesa 12" autoFocus />
          <Input label="Nome do Cliente (Opcional)" placeholder="Ex: João da Silva" />
          <div className="flex justify-end gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              leftIcon={<CheckCircle className="w-4 h-4" />}
              onClick={() => {
                alert('Comanda aberta com sucesso!')
                setIsModalOpen(false)
              }}
            >
              Confirmar Abertura
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
