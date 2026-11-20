# Design System e Guia de Estilos — Hstronomia

Este documento estabelece a identidade visual, padrões de interface (UI), convenções de experiência do usuário (UX) e tokens do Tailwind CSS para todas as aplicações do **Hstronomia** (Painel do Dono, Interface do Garçom e KDS da Cozinha).

---

## 1. Identidade Visual e Atmosfera

- **Conceito**: Fast-casual contemporâneo, hamburguerias, pizzarias e restaurantes ágeis.
- **Personalidade**: Dinâmica, confiável, prática e de alta produtividade.
- **Paleta Central**: **Vermelho Carmim** (energia, apetite e ação primária) combinado com **Cinzas Neutros / Zinc** (clareza, legibilidade e profissionalismo).
- **Abordagem de Componentes**: **Compacto & Administrativo** — foco em alta densidade de informação, bordas sutis (`rounded-md`), dados alinhados e sem espaço ocioso desnecessário.

---

## 2. Estratégia de Temas (Híbrido Contextual)

| Perfil / Ambiente | Tema Padrão | Justificativa de UX |
| :--- | :--- | :--- |
| **Cozinha (KDS)** | **Dark Mode Obrigatório** (`bg-zinc-950`) | Ambiente quente, telas brilhantes e reflexos de inox. O tema escuro de alto contraste reduz fadiga visual e destaca imediatamente pedidos pendentes e timers. |
| **Garçom (Mobile)** | **Light Mode** (com suporte a Dark) | Uso ágil no salão com iluminação variável. Foco em botões nítidos e fácil leitura de comandas e mesas. |
| **Painel do Dono (Admin)** | **Light Mode** (com chave seletora) | Leitura confortável de relatórios financeiros, gráficos e tabelas densas durante o dia. |

---

## 3. Paleta de Cores e Tokens Tailwind CSS

### 3.1. Cor Primária — Vermelho Carmim (Brand & Ação Principal)

| Token | Classe Tailwind | Hex Aproximado | Aplicação |
| :--- | :--- | :--- | :--- |
| **Primary Default** | `bg-red-600` / `text-red-600` | `#dc2626` | Botões primários, CTA principal, links ativos, destaques |
| **Primary Hover** | `hover:bg-red-700` | `#b91c1c` | Estado hover de botões e links |
| **Primary Active** | `active:bg-red-800` | `#991b1b` | Clique ativo / pressionamento |
| **Primary Soft** | `bg-red-50` / `text-red-700` | `#fef2f2` | Badges de destaque, alertas suaves, chips selecionados |
| **Primary Border** | `border-red-300` / `border-red-600` | `#fca5a5` / `#dc2626` | Contornos de foco e bordas ativas |

### 3.2. Superfícies e Neutros (Escala Zinc)

| Elemento | Light Mode | Dark Mode (Cozinha KDS) |
| :--- | :--- | :--- |
| **Fundo da Página** | `bg-zinc-50` | `bg-zinc-950` |
| **Fundo de Cards / Modais** | `bg-white` | `bg-zinc-900` |
| **Fundo Secundário / Inputs** | `bg-zinc-100` | `bg-zinc-800` |
| **Bordas e Divisores** | `border-zinc-200` | `border-zinc-800` |
| **Bordas Suaves** | `border-zinc-100` | `border-zinc-850` |
| **Texto Principal** | `text-zinc-900` | `text-zinc-100` |
| **Texto Secundário / Labels**| `text-zinc-500` | `text-zinc-400` |
| **Texto Desabilitado** | `text-zinc-400` | `text-zinc-600` |

### 3.3. Convenção Semáforo para Status de Pedidos e Comandas

| Status | Cor Base | Classe Badge (Light) | Classe Badge (Dark / KDS) | Significado Operacional |
| :--- | :--- | :--- | :--- | :--- |
| **Pronto / Fechada / Ativo** | Verde (`emerald`) | `bg-emerald-50 text-emerald-700 border-emerald-200` | `bg-emerald-950/60 text-emerald-300 border-emerald-800` | Pedido pronto para entrega; comanda paga; item disponível |
| **Em Preparo / Atenção** | Amarelo/Laranja (`amber`) | `bg-amber-50 text-amber-800 border-amber-200` | `bg-amber-950/60 text-amber-300 border-amber-800` | Item sendo cozinhado; mesa aguardando atendimento |
| **Pendente / Aberta** | Azul (`sky`/`blue`) | `bg-sky-50 text-sky-700 border-sky-200` | `bg-sky-950/60 text-sky-300 border-sky-800` | Pedido recém-chegado à fila KDS; comanda aberta consumindo |
| **Atrasado / Cancelado / Erro** | Vermelho (`red`) | `bg-red-50 text-red-700 border-red-200` | `bg-red-950/60 text-red-300 border-red-800` | Pedido excedeu tempo tolerado; comanda cancelada |

---

## 4. Tipografia e Numerais

- **Fonte Principal**: `font-sans` (Inter, Roboto, sans-serif do sistema).
- **Alinhamento Numérico Obrigatório**:
  - Preços em R$, quantidades, horários e números de comanda **devem obrigatoriamente** usar classe `tabular-nums` ou `font-mono` para alinhamento vertical perfeito em tabelas e listas.
- **Hierarquia de Tamanhos**:
  - `text-xs`: Badges, tags de observações, metadados de rodapé.
  - `text-sm`: Textos padrão de tabelas, formulários, labels e botões secundários.
  - `text-base`: Texto corrido, cabeçalhos de itens de comanda.
  - `text-lg` / `text-xl`: Títulos de cards, identificação de mesas (`Mesa 04`).
  - `text-2xl` / `text-3xl`: Valores de faturamento total, timers grandes no KDS.

---

## 5. Padrão de Formato dos Componentes (Compacto & Administrativo)

### 5.1. Bordas e Cantos
- **Padrão Oficial**: `rounded-md` (4px a 6px).
- **Badges e Chips**: `rounded-full` ou `rounded` (compactos).
- **Proibição**: Evitar cantos excessivamente redondos (`rounded-2xl`, `rounded-3xl`) em painéis de gestão para preservar densidade de dados.

### 5.2. Botões Padronizados

```tsx
// 1. Botão Primário (Ação Principal / Enviar / Fechar Comanda)
<button className="inline-flex items-center justify-center gap-2 px-3.5 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 active:bg-red-800 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 disabled:opacity-50">
  Confirmar Pedido
</button>

// 2. Botão Secundário (Ação Neutra / Cancelar / Voltar)
<button className="inline-flex items-center justify-center gap-2 px-3 py-1.5 text-sm font-medium text-zinc-700 bg-white border border-zinc-300 rounded-md hover:bg-zinc-50 active:bg-zinc-100 transition-colors dark:bg-zinc-800 dark:text-zinc-200 dark:border-zinc-700 dark:hover:bg-zinc-750">
  Cancelar
</button>

// 3. Botão de Ação Rápida no KDS (Dark Mode)
<button className="w-full py-2.5 px-4 text-sm font-semibold text-emerald-950 bg-emerald-400 hover:bg-emerald-300 active:bg-emerald-500 rounded-md transition-colors">
  Marcar como Pronto
</button>
```

### 5.3. Campos de Entrada (Inputs)
- Altura controlada (`h-9` ou `py-1.5 px-3`).
- Borda fina `border-zinc-300` com anel de foco no vermelho: `focus:ring-1 focus:ring-red-500 focus:border-red-500`.

### 5.4. Cards e Containers
- `border border-zinc-200 dark:border-zinc-800` com sombra sutil `shadow-sm`.
- Padding padronizado: `p-4` para cartões gerais, `p-3` para cartões compactos de comanda/item.

---

## 6. Diretrizes de UX Específicas por Perfil

### 6.1. Garçom (Mobile-First)
- **Área de Toque**: Todos os botões clicáveis têm altura mínima de `44px` para uso confortável com uma mão.
- **Controle de Quantidade**: Botões grandes de `+` e `-` com feedback tátil/visual imediato ao adicionar rodadas de itens.
- **Campo de Observação Rápido**: Chips com observações comuns ("Sem gelo", "Sem cebola", "Ao ponto", "Gelo e limão") para evitar digitação demorada.
- **Acesso por PIN**: Teclado numérico virtual rápido de 4 dígitos na tela de login operacional.

### 6.2. Cozinha KDS (Monitor / Tablet First em Dark Mode)
- **Visibilidade à Distância**: Letras grandes (`text-base` a `text-xl`) em títulos de itens e observações em amarelo de alto contraste (`text-amber-300`).
- **Cronômetro Visual de Espera**:
  - `< 10 min`: Texto verde suave.
  - `10 a 20 min`: Texto amarelo/alerta.
  - `> 20 min`: Fundo do cabeçalho pulsando em vermelho suave.
- **Avanço em 1 Clique**: Um toque largo para mudar de `pendente` ➔ `em_preparo` ➔ `pronto`.

### 6.3. Painel do Dono (Desktop-First)
- **Visão Geral Diária**: Cards no topo com Faturamento Bruto, Despesas do Dia, Comandas Abertas e Ticket Médio.
- **Tabelas com Densidade**: Linhas compactas com paginação e busca instantânea de itens de cardápio e comandas.
- **Ações Críticas Protegidas**: Confirmações com modais rápidos para cancelamento de comanda ou alteração de preços do cardápio.

---

## 7. Padronização Estrita de Ícones e Proibição de Emojis

### 7.1. Proibição Absoluta de Emojis na Interface
- ❌ **É TERMINANTEMENTE PROIBIDO usar emojis** (ex: 🍽️, 🍔, 💰, 🟢, 🔴, ⚠️, 🧑‍🍳, etc.) em qualquer lugar da interface: botões, títulos, cards, tabelas, modais, mensagens de erro ou toasts.
-  **Substituição Obrigatória**: Status, ações e indicadores devem ser representados exclusivamente por componentes de UI limpos: **Badges semânticos com texto objetivo** e/ou **ícones vetorizados discretos da biblioteca `lucide-react`**.

### 7.2. Biblioteca Única de Ícones: `lucide-react`
- Proibido misturar bibliotecas (não usar FontAwesome, Material Icons, Heroicons ou SVGs avulsos). **Todo ícone deve vir do `lucide-react`**.
- **Espessura do Traço Padronizada**: `strokeWidth={2}` (ou `1.75` para ícones grandes).
- **Tamanhos Padronizados (Sem Exceção)**:
  - `w-4 h-4`: Dentro de botões, badges, inputs e células de tabelas.
  - `w-5 h-5`: Em itens de navegação (sidebar, navbar, topbar) e cabeçalhos de cards.
  - `w-6 h-6`: Apenas em ícones de destaque isolados (ex: modal de confirmação crítica ou avatar).
- **Mapeamento de Ícones Oficiais**:
  - Mesas e Salão: `LayoutGrid`, `Utensils`, `Receipt`.
  - Cozinha (KDS): `ChefHat`, `Clock`, `Flame`, `CheckCircle2`.
  - Financeiro e Caixa: `DollarSign`, `TrendingUp`, `TrendingDown`, `CreditCard`.
  - Ações Globais: `Plus`, `Trash2`, `Edit3`, `Search`, `ArrowLeft`, `LogOut`, `RefreshCw`, `AlertCircle`.

---

## 8. Consistência Visual Unificada (Zero "Software Misto")

Todas as telas do sistema (**Login**, **Painel do Dono**, **Terminal do Garçom** e **Cozinha KDS**) **devem obrigatoriamente parecer partes do mesmo produto coeso**. Não é permitido que uma tela pareça um dashboard corporativo e outra pareça um app isolado com estilos conflitantes.

### 8.1. Regras de Unificação Estrutural
1. **Componentes Base Compartilhados (`src/components/ui/`)**:
   - Todas as telas **devem reutilizar os mesmos componentes atômicos**: `<Button>`, `<Input>`, `<Select>`, `<Card>`, `<Badge>`, `<Modal>` e `<EmptyState>`. Nenhuma tela deve inventar um estilo de botão ou input diferente do restante do sistema.
2. **Estrutura de Cabeçalho Consistente (TopBar)**:
   - Todas as telas autenticadas (Garçom, Cozinha e Dono) compartilham o mesmo padrão de TopBar:
     - Fundo com borda inferior sutil (`border-b border-zinc-200 dark:border-zinc-800`).
     - Lado esquerdo: Marca **Hstronomia** com acento em vermelho (`text-red-600 font-bold`) + identificador do Restaurante atual.
     - Lado direito: Perfil logado (`Garçom`, `Cozinha` ou `Dono`), badge de status da conexão e botão discreto de encerramento de sessão (`LogOut`).
3. **Escala de Cinzas Universal**:
   - Usar **apenas a família Zinc do Tailwind** (`zinc-50` até `zinc-950`). Proibido misturar `slate`, `gray`, `neutral` ou `stone` em arquivos diferentes.
4. **Espaçamento e Densidade Idênticos**:
   - Gaps de grids padronizados (`gap-4` ou `gap-6`).
   - Padding de containers e páginas alinhado (`p-4` a `p-6` no desktop, `p-3` a `p-4` no mobile).
5. **Tipografia Unificada**:
   - Sem fontes personalizadas exóticas. Apenas `font-sans` do sistema para textos e `tabular-nums` / `font-mono` para valores numéricos e preços em todas as telas.

---

## 9. Diretrizes Anti-AI Slop (O Que NUNCA Fazer)

Para evitar que a interface pareça um template genérico de IA ("AI Slop"), poluído, lento ou infantil, **as seguintes práticas são expressamente proibidas**:

### 9.1. Proibições Visuais
1. **Sem Gradientes Genéricos de IA**:
   - ❌ **Proibido**: `bg-gradient-to-r from-purple-500 via-pink-500 to-red-500` em botões, textos ou fundos.
   -  **Correto**: Cores sólidas e deliberadas (`bg-red-600`, `bg-zinc-900`, `bg-white`).
2. **Sem Glassmorphism / Blur Exagerado**:
   - ❌ **Proibido**: `backdrop-blur-md bg-white/20 border-white/30`. Torna a leitura péssima sob luz forte do salão ou lâmpadas de cozinha.
   -  **Correto**: Superfícies opacas e legíveis (`bg-white` no light, `bg-zinc-900` no dark).
3. **Sem Sombras Gigantescas e Coloridas**:
   - ❌ **Proibido**: `shadow-2xl shadow-red-500/50`. Parece mockup de Dribbble impraticável.
   -  **Correto**: Sombras utilitárias e discretas (`shadow-sm` para cards, `shadow-md` para modais).
4. **Sem Cantos de Pílula Excessivos em Painéis**:
   - ❌ **Proibido**: `rounded-3xl` ou `rounded-2xl` em cards e modais administrativos.
   -  **Correto**: `rounded-md` (4px a 6px). A interface deve transmitir seriedade de ERP/PDV, não de brinquedo.

### 9.2. Proibições de UX e Comportamento
5. **Sem Hero Sections Vizinhas e Banners de Boas-Vindas Inúteis**:
   - ❌ **Proibido**: Colocar "Bem-vindo ao Hstronomia! O poder da gastronomia em suas mãos!" ocupando metade da tela do garçom ou da cozinha.
   -  **Correto**: Acesso direto à ação. O garçom abre a tela e vê mesas; a cozinha abre a tela e vê pedidos; o dono abre a tela e vê números.
6. **Sem Animações Lentas em Fluxos Operacionais**:
   - ❌ **Proibido**: `transition-all duration-500` ou animações de bounce/fade demoradas ao adicionar itens ou fechar comanda.
   -  **Correto**: Transições quase imperceptíveis (`duration-150` ou instantâneo). O garçom precisa lançar 10 pedidos em segundos no salão lotado.
7. **Sem Poluição de Ícones**:
   - ❌ **Proibido**: Colocar um ícone na frente de cada palavra, label ou coluna de tabela.
   -  **Correto**: Ícone só onde agrega significado e orientação espacial rápida.
8. **Sem Textos Motivacionais e Copywriting Vazio de IA**:
   - ❌ **Proibido**: "Potencialize seus lucros hoje mesmo", "Descubra a harmonia na sua cozinha".
   -  **Correto**: Rótulos técnicos, concisos e diretos: "Total Faturado", "Despesas do Dia", "Tempo Médio de Espera", "Fechar Comanda".
9. **Estados Vazios (Empty States) Práticos**:
   - ❌ **Proibido**: Ilustrações gigantes SVG de astronautas ou personagens tristes dizendo "Ops, nada por aqui!".
   -  **Correto**: Ícone simples discreto, uma linha explicativa e um botão de ação claro (ex: `Nenhuma mesa com comanda aberta no momento. [ + Abrir Comanda ]`).

---

## 10. Estados de Carregamento: Skeletons Obrigatórios (Zero Layout Shift)

Para garantir uma sensação de velocidade instantânea e evitar saltos visuais bruscos na tela (*Cumulative Layout Shift - CLS*), **o uso de Skeletons é obrigatório em todas as telas com busca de dados via TanStack Query**.

### 10.1. Regras de Carregamento
1. ❌ **Proibido usar spinners circulares centralizados que bloqueiam a tela inteira**: Eles passam a impressão de lentidão e quebram o layout quando o dado chega.
2.  **Obrigatório espelhar o layout final**: O Skeleton deve possuir exatamente a mesma geometria, altura e contorno do card, tabela ou item que vai ocupar aquele espaço.
3. **Animação Padronizada**: Pulso suave com `animate-pulse` nativo do Tailwind.
4. **Cores do Skeleton**:
   - Light Mode: `bg-zinc-200/80 rounded-md`
   - Dark Mode (Cozinha KDS): `bg-zinc-800/80 rounded-md`

### 10.2. Componente Atômico `<Skeleton>` (`src/components/ui/Skeleton.tsx`)
```tsx
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({ className = '', ...props }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-zinc-200 dark:bg-zinc-800 rounded-md ${className}`}
      {...props}
    />
  );
}
```

### 10.3. Padrões de Skeleton por Tipo de Tela

```tsx
// 1. Skeleton de Cards do Dashboard (Dono)
<div className="p-4 border border-zinc-200 dark:border-zinc-800 rounded-md space-y-3">
  <div className="flex justify-between items-center">
    <Skeleton className="h-4 w-28" />
    <Skeleton className="h-4 w-4 rounded-full" />
  </div>
  <Skeleton className="h-8 w-36" />
  <Skeleton className="h-3 w-20" />
</div>

// 2. Skeleton de Linha de Tabela (Cardápio / Despesas / Comandas)
<div className="flex items-center justify-between py-3 px-4 border-b border-zinc-200 dark:border-zinc-800">
  <div className="space-y-1.5">
    <Skeleton className="h-4 w-44" />
    <Skeleton className="h-3 w-64" />
  </div>
  <div className="flex items-center gap-3">
    <Skeleton className="h-4 w-16" />
    <Skeleton className="h-6 w-14" />
  </div>
</div>

// 3. Skeleton de Card de Mesa (Garçom - Mobile)
<div className="p-4 border border-zinc-200 rounded-md space-y-2">
  <div className="flex justify-between">
    <Skeleton className="h-5 w-20" />
    <Skeleton className="h-5 w-14" />
  </div>
  <Skeleton className="h-4 w-28" />
  <Skeleton className="h-8 w-full mt-2" />
</div>

// 4. Skeleton de Pedido KDS (Cozinha - Dark Mode)
<div className="p-4 bg-zinc-900 border border-zinc-800 rounded-md space-y-3">
  <div className="flex justify-between">
    <Skeleton className="h-5 w-24" />
    <Skeleton className="h-5 w-16" />
  </div>
  <div className="space-y-2">
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
  </div>
  <Skeleton className="h-9 w-full mt-2" />
</div>
```

---

Este guia é a referência visual vinculativa para todas as issues e componentes de frontend a serem desenvolvidos no repositório.
