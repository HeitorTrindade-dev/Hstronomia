# 0003 — Setup Inicial do Frontend (React, Vite, TypeScript, Tailwind)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Google DeepMind)
- **Tipo de Mudança**: Setup / Frontend / UI
- **Issue Vinculada**: [#3](https://github.com/HeitorTrindade-dev/Hstronomia/issues/3)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #3: inicialização da aplicação cliente SPA com React 18+, Vite, TypeScript, Tailwind CSS e estruturação da arquitetura de pastas definida em `agents/frontend.md`.

---

## 2. Decisões Técnicas Tomadas

1. **Stack e Ferramentas**:
   - `react` 18+ e `react-dom`.
   - `vite` como build tool e bundler.
   - `typescript` para tipagem estática.
   - `tailwindcss` e `autoprefixer` para estilização utilitária.
   - `lucide-react` para ícones da interface.
   - `axios` e `@tanstack/react-query` para comunicação e cache de requisições.
   - `react-router-dom` para navegação SPA.

2. **Variáveis de Ambiente**:
   - Criado `frontend/.env.example` com `VITE_API_URL=http://localhost:8000/api/v1`.
   - Configurado `frontend/src/vite-env.d.ts` para tipagem do `import.meta.env`.

3. **Arquitetura de Pastas (`frontend/src/`)**:
   - `components/`, `contexts/`, `hooks/`, `pages/`, `services/`, `types/`.

4. **Validação de Build**:
   - Executado `npm run build` (`tsc -b && vite build`) com 100% de sucesso e zero vulnerabilidades no `npm audit`.

---

## 3. Arquivos Criados / Modificados
- [`frontend/package.json`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/package.json): Dependências e scripts de execução.
- [`frontend/tsconfig.json`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/tsconfig.json): Configuração do compilador TypeScript.
- [`frontend/vite.config.ts`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/vite.config.ts): Configuração do Vite.
- [`frontend/tailwind.config.js`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/tailwind.config.js): Configuração do Tailwind CSS.
- [`frontend/postcss.config.js`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/postcss.config.js): Plugin PostCSS para Tailwind.
- [`frontend/index.html`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/index.html): HTML base com viewport mobile.
- [`frontend/.env.example`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/.env.example): Template de variáveis de ambiente.
- [`frontend/src/App.tsx`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/App.tsx): Componente inicial com ícone Lucide e status da API.
- [`frontend/src/main.tsx`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/main.tsx): Ponto de entrada do React.
- [`frontend/src/index.css`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/index.css): Diretivas do Tailwind.
- [`frontend/src/vite-env.d.ts`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/vite-env.d.ts): Tipos do Vite client.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0003.
