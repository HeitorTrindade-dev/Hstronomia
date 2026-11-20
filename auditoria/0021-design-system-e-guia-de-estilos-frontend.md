# 0021 — Design System e Guia de Estilos Frontend

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity
- **Status**: Concluído

---

## 1. Contexto e Motivação
Com a finalização de todas as etapas críticas do backend (autenticação JWT, PINs operacionais, comandas, KDS, financeiro e hardening de segurança OWASP), iniciou-se a preparação para o desenvolvimento do Frontend.
Para garantir coesão visual, produtividade e alinhamento estético entre todas as telas operacionais (Garçom mobile, Cozinha KDS tablet/monitor e Painel do Dono desktop), foi realizado um alinhamento interativo de design com o usuário.

---

## 2. Decisões de Design e Identidade Visual

1. **Paleta Central**:
   - **Vermelho Carmim** (`bg-red-600`, `hover:bg-red-700`, `active:bg-red-800`, `bg-red-50`) como cor primária de destaque, apetite e ação, complementado por **Cinzas Neutros / Zinc** (`zinc-50` a `zinc-950`).
   - Identidade alinhada a hamburguerias, pizzarias e fast-casual contemporâneo.

2. **Estratégia Híbrida de Temas**:
   - **Cozinha KDS**: **Dark Mode obrigatório** (`bg-zinc-950`) de alto contraste, reduzindo reflexos e fadiga visual em cozinhas quentes e iluminadas.
   - **Garçom e Painel do Dono**: **Light Mode clean** por padrão (`bg-zinc-50` / `bg-white`), com suporte a alternância para modo escuro.

3. **Formato dos Componentes (Compacto & Administrativo)**:
   - Bordas moderadas e sóbrias (`rounded-md`, 4px a 6px).
   - Alta densidade de informação para formulários rápidos, tabelas financeiras e listas de pedidos.
   - Tipografia com alinhamento numérico obrigatório (`tabular-nums` ou `font-mono`) em preços e horários.

4. **Convenção Semáforo para Status**:
   - Verde (`emerald`): Pedido pronto, comanda fechada/paga, item disponível.
   - Amarelo/Laranja (`amber`): Pedido em preparo, atenção.
   - Azul (`sky`/`blue`): Pedido pendente, comanda aberta em consumo.
   - Vermelho (`red`): Pedido atrasado, comanda cancelada.

5. **Padronização Estrita de Ícones e Proibição de Emojis**:
   - Proibição absoluta do uso de emojis na interface (nada de emojis em botões, tabelas, modais ou mensagens de erro).
   - Uso exclusivo da biblioteca `lucide-react` com dimensões e traços uniformes (`w-4 h-4` para ações/tabelas, `w-5 h-5` para navegação, `strokeWidth={2}`).

6. **Consistência Visual Unificada (Zero "Software Misto")**:
   - Todas as telas compartilham os mesmos componentes atômicos em `src/components/ui/` (`<Button>`, `<Input>`, `<Select>`, `<Card>`, `<Badge>`, `<Modal>`).
   - Padrão idêntico de cabeçalho TopBar, espaçamentos unificados e paleta exclusiva na família `zinc` + `red-600`.

7. **Estados de Carregamento: Skeletons Obrigatórios**:
   - Proibição de spinners de tela cheia que causam saltos bruscos de layout (*Cumulative Layout Shift*).
   - Obrigatoriedade de Skeletons espelhando a geometria exata dos cards, tabelas, mesas e cards da fila KDS via `animate-pulse` suave (`bg-zinc-200` no light e `bg-zinc-800` no dark).

8. **Diretrizes Anti-AI Slop**:
   - Proibição de gradientes roxos/rosas genéricos, glassmorphism/blurs ilegíveis, sombras gigantescas fluorescentes e bordas infantis `rounded-3xl`.
   - Proibição de banners de boas-vindas vazios, animações lentas que atrasam a operação e copywriting motivacional corporativo. Foco total em utilidade, alta densidade e rapidez de PDV real.

---

## 3. Arquivos Criados ou Modificados

- `estilos.md`: Guia canônico completo do Design System do Hstronomia com tokens Tailwind, snippets de componentes e diretrizes por perfil.
- `agents/frontend.md`: Atualizado com referência vinculativa ao `estilos.md`.
- `auditoria/0021-design-system-e-guia-de-estilos-frontend.md`: Este registro de auditoria.
- `auditoria/indice.md`: Indexação da entrada 0021.
