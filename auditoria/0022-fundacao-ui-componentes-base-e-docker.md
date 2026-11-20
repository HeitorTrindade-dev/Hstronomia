# 0022 — Fundação de UI, Componentes Base, TopBar Unificada e Orquestração Docker

**Data:** 2026-11-20  
**Autor:** Heitor / Antigravity Agent  
**Issue Relacionada:** [#49 - [Frontend] Fundacao de UI: Componentes Base, TopBar Unificada e Skeletons](https://github.com/HeitorTrindade-dev/Hstronomia/issues/49)  
**Branch:** `feat/49-fundacao-ui-componentes`

---

## 1. Contexto e Motivação

Com a conclusão da especificação oficial do Design System em `estilos.md` e a aprovação das diretrizes anti-AI-slop, a Issue #49 inaugura a camada visual do **Hstronomia**.
O objetivo desta etapa é construir a fundação atômica e estrutural da interface com consistência rigorosa, eliminando padrões genéricos de IA, respeitando as boas práticas modernas de acessibilidade web (Modern Web Guidance) e provendo orquestração Docker completa para execução local imediata pelo usuário.

---

## 2. Implementações Realizadas

### 2.1. Configuração do Tailwind CSS e CSS Global
- **Dark Mode via classe (`darkMode: 'class'`)**: Essencial para a Cozinha KDS operar em modo escuro puro (`bg-zinc-950`).
- **Paleta Carmim Oficial**: Configuração das cores de marca (`brand-50` a `brand-900`) e suporte nativo às famílias `zinc`, `red`, `emerald`, `amber` e `sky`.
- **Modern Web Guidance para Modais**:
  - `dialog:modal { overscroll-behavior: contain; }`
  - `dialog::backdrop { background-color: rgba(24, 24, 27, 0.6); backdrop-filter: blur(2px); overflow: hidden; overscroll-behavior: contain; }`
  - Prevenção de encadeamento de rolagem sem recorrer a travas manuais no `body`.

### 2.2. Componentes Base Atômicos (`src/components/ui/`)
1. **`Button.tsx`**:
   - Variantes: `primary` (carmim `bg-red-600`), `secondary` (`border-zinc-300`), `danger` (`bg-red-700`), `ghost` (`hover:bg-zinc-100`).
   - Tamanhos: `sm` (h-8), `md` (h-9), `lg` (h-10).
   - Suporte a `isLoading` (spinner `Loader2` animado), `disabled`, `leftIcon` e `rightIcon`.
2. **`Input.tsx`**:
   - Design compacto (`h-9`), bordas discretas, foco carmim (`focus:ring-red-500`).
   - Acessibilidade integrada via `useId()`, `aria-invalid` e `aria-describedby` para `error` e `hint`.
   - Suporte a ícones de prefixo e sufixo com espaçamento proporcional.
3. **`Select.tsx`**:
   - Seletor nativo estilizado compacto, suporte a lista de `options` ou `children`, com estados de erro e acessibilidade.
4. **`Card.tsx`**:
   - Container modular de superfície (`rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm`).
   - Subcomponentes: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
5. **`Badge.tsx`**:
   - Semáforo operacional estrito: `emerald` (Pronto/Aberto), `amber` (Em Preparo/Pendente), `sky` (Entregue/Info), `red` (Cancelado/Fechada), `zinc` (Neutro).
   - Indicador com ponto (`withDot`) e tipografia monoespaçada/tabular (`tabular-nums`).
6. **`Modal.tsx`**:
   - Diálogo acessível baseado na tag nativa `<dialog>` com `showModal()` e `close()`.
   - Suporte ao atributo `closedby="any"` e fallback seguro de light-dismiss (clique no backdrop).
   - `aria-labelledby` vinculado ao título e botão de fechar acessível (`aria-label="Fechar diálogo"`).
7. **`Skeleton.tsx`**:
   - Blocos com animação pulsante (`animate-pulse bg-zinc-200 dark:bg-zinc-800 rounded-md`).
   - Componentes utilitários: `SkeletonCard` e `SkeletonTableRow` para espelhar a geometria exata das telas e anular o Cumulative Layout Shift (CLS).
8. **`EmptyState.tsx`**:
   - Layout discreto e limpo com ícone `lucide-react`, título, descrição concisa e botão de ação opcional. Sem emojis.

### 2.3. Componente Estrutural de TopBar (`src/components/layout/TopBar.tsx`)
- Barra superior universal presente em todas as telas:
  - Marca Hstronomia com ícone `UtensilsCrossed` carmim.
  - Indicador contextual do restaurante ativo (`/ Cantina Famiglia`).
  - Badge do perfil conectado (`Dono`, `Garçom`, `Cozinha KDS`).
  - Alternador dinâmico de tema Claro / Escuro.
  - Botão de logout com ícone `LogOut`.

### 2.4. Vitrine Interativa (`src/App.tsx`)
- Demonstração visual de 100% dos componentes base criados, permitindo alternar tema, simular papéis, testar botões com loading, preencher formulários e disparar o diálogo modal.

### 2.5. Containerização e Orquestração Docker
- **`backend/Dockerfile`**: Imagem Python 3.12-slim com execução de migrações (`alembic upgrade head`) e servidor Uvicorn na porta 8000.
- **`frontend/Dockerfile` & `frontend/nginx.conf`**: Build multi-stage Node 20 + NGINX alpine servindo a SPA na porta 5173 com proxy reverso transparente para `/api/`.
- **`docker-compose.yml`**: Orquestra PostgreSQL 15, Backend FastAPI e Frontend NGINX com healthcheck do banco.

---

## 3. Arquivos Criados e Modificados

- `frontend/tailwind.config.js`: darkMode class e extensão de cores brand carmim.
- `frontend/src/index.css`: regras Modern Web Guidance para dialog modal e backdrop.
- `frontend/src/components/ui/Button.tsx`: componente de botão atômico.
- `frontend/src/components/ui/Input.tsx`: componente de entrada de texto com acessibilidade.
- `frontend/src/components/ui/Select.tsx`: componente de seleção compacto.
- `frontend/src/components/ui/Card.tsx`: componente de superfície e cartões.
- `frontend/src/components/ui/Badge.tsx`: componente de status com semáforo operacional.
- `frontend/src/components/ui/Modal.tsx`: diálogo nativo acessível com backdrop.
- `frontend/src/components/ui/Skeleton.tsx`: elementos pulsantes contra layout shift.
- `frontend/src/components/ui/EmptyState.tsx`: tela de listagem vazia.
- `frontend/src/components/ui/index.ts`: barril de exportação de UI.
- `frontend/src/components/layout/TopBar.tsx`: barra de navegação e contexto universal.
- `frontend/src/components/layout/index.ts`: barril de exportação de layout.
- `frontend/src/App.tsx`: vitrine interativa da fundação de UI.
- `frontend/nginx.conf`: configuração de servidor web e proxy reverso.
- `frontend/Dockerfile`: containerização de produção do frontend.
- `backend/Dockerfile`: containerização do backend com migrações automáticas.
- `docker-compose.yml`: orquestração completa dos 3 serviços.
- `auditoria/0022-fundacao-ui-componentes-base-e-docker.md`: registro desta auditoria.
- `auditoria/indice.md`: índice atualizado.

---

## 4. Validação e Qualidade

- **TypeScript / Vite Build**: Compilação sem nenhum erro ou aviso (`tsc -b && vite build` concluído com sucesso).
- **Testes Backend**: 65/65 testes automatizados aprovados no `pytest`.
- **Zero Emojis**: Rigorosamente respeitado em toda a base de código e documentação.
- **Docker Compose**: Serviços rodando e acessíveis em `http://localhost:5173` (Frontend) e `http://localhost:8000` (Backend).
