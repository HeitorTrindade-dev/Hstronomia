# 0023 — Roteamento, Cliente HTTP Axios e Contexto de Autenticação Multi-Perfil

**Data:** 2026-11-20  
**Autor:** Heitor / Antigravity Agent  
**Issue Relacionada:** [#50 - [Frontend] Roteamento, Cliente HTTP e Contexto de Autenticacao Multi-Perfil](https://github.com/HeitorTrindade-dev/Hstronomia/issues/50)  
**Branch:** `feat/50-roteamento-auth-context`

---

## 1. Contexto e Motivação

Após a entrega da Fundação de UI e componentes atômicos (Issue #49), tornou-se necessário implementar a infraestrutura essencial de navegação, comunicação HTTP e controle de sessão do **Hstronomia**.
O sistema opera em modelo multi-perfil estrito:
- **Dono**: Acesso irrestrito a gestão multi-restaurante, configurações de PIN, cardápio completo e métricas financeiras via token JWT de longa duração.
- **Garçom**: Acesso operacional focado em salão, comandas e pedidos via PIN numérico.
- **Cozinha (KDS)**: Acesso operacional focado em fila de pedidos em tempo real em Dark Mode obrigatório via PIN numérico.

A Issue #50 estabelece a espinha dorsal de roteamento e estado global que suportará todas as telas do sistema.

---

## 2. Implementações Realizadas

### 2.1. Tipos TypeScript Estritos (`frontend/src/types/auth.ts`)
- Definição formal das interfaces:
  - `UserRole`: `'dono' | 'garcom' | 'cozinha'`
  - `Dono`: Identificador, nome, email e timestamp de criação.
  - `Restaurante`: Identificador, nome e slug do restaurante ativo.
  - `LoginDonoCredentials`, `CadastroDonoData`, `LoginOperacionalCredentials`.
  - `TokenResponse` e `AuthMeResponse` espelhando os schemas Pydantic do backend.
  - `UserSession`: Estrutura do estado da sessão.

### 2.2. Cliente HTTP Axios com Interceptors (`frontend/src/services/api.ts`)
- Instância Axios configurada lendo `VITE_API_URL` com fallback para `/api/v1`.
- **Request Interceptor**: Injeção automática do Bearer Token nos headers (`Authorization: Bearer <token>`) a partir de `localStorage`.
- **Response Interceptor**: Captura de status `401 Unauthorized` com limpeza segura do `localStorage` e redirecionamento para `/login` (exceto para requisições de autenticação, preservando mensagens de erro de formulário).

### 2.3. Serviços de API de Autenticação (`frontend/src/services/auth.ts`)
- Integração tipada com os endpoints do backend:
  - `loginDono()`: `POST /api/v1/auth/login`
  - `cadastrarDono()`: `POST /api/v1/auth/cadastrar`
  - `loginOperacional()`: `POST /api/v1/auth/operacional`
  - `getMe()`: `GET /api/v1/auth/me`

### 2.4. Contexto de Autenticação Global (`frontend/src/contexts/AuthContext.tsx`)
- Gerenciamento de estado reativo: `token`, `role`, `user`, `restaurante`, `isAuthenticated`, `isLoading`.
- **Restauração Automática de Sessão**: No carregamento inicial da aplicação (`useEffect`), se existir um token armazenado, a aplicação consome `/api/v1/auth/me` para validar a sessão e preencher o perfil do usuário e restaurante ativo antes de liberar a renderização protegida.
- Métodos integrados: `loginDono`, `loginOperacional`, `logout`, `setRestauranteAtivo`.

### 2.5. Componente de Guarda de Rota (`frontend/src/components/layout/ProtectedRoute.tsx`)
- Prevenção de flashes visuais: exibe layout skeleton enquanto `isLoading` valida a sessão.
- Redirecionamento de não autenticados para `/login` com preservação da URL requisitada no `state.from`.
- **RBAC (Role-Based Access Control)**: Bloqueia acesso cruzado não autorizado (ex: Garçom tentando acessar `/admin`) e redireciona o usuário para o painel de sua respectiva role.

### 2.6. Roteamento Completo da Aplicação (`frontend/src/App.tsx`)
- Configuração do React Router v7 com:
  - Rota raiz `/` com redirecionamento inteligente baseado no status de autenticação e role.
  - Rotas públicas: `/login` ([LoginPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/auth/LoginPage.tsx)), `/cadastrar` ([CadastroPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/auth/CadastroPage.tsx)), `/acesso/:slug` ([AcessoPinPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/auth/AcessoPinPage.tsx)) e `/design-system` ([DesignSystemPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/DesignSystemPage.tsx)).
  - Rotas privadas: `/admin/*` ([AdminDashboardPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/admin/AdminDashboardPage.tsx)), `/garcom/*` ([GarcomDashboardPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/garcom/GarcomDashboardPage.tsx)) e `/cozinha/*` ([CozinhaKdsPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/cozinha/CozinhaKdsPage.tsx)).
  - Rota 404: `*` ([NotFoundPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/NotFoundPage.tsx)).

---

## 3. Arquivos Criados e Modificados

- `frontend/src/types/auth.ts`: tipos de autenticação, roles e sessões.
- `frontend/src/services/api.ts`: cliente Axios, constantes de storage e interceptors.
- `frontend/src/services/auth.ts`: funções de chamada aos endpoints de auth.
- `frontend/src/contexts/AuthContext.tsx`: provider e hook `useAuth()`.
- `frontend/src/components/layout/ProtectedRoute.tsx`: guarda de rotas por role.
- `frontend/src/components/layout/index.ts`: exportação de layout atualizada.
- `frontend/src/pages/auth/LoginPage.tsx`: tela de login do dono.
- `frontend/src/pages/auth/CadastroPage.tsx`: tela de cadastro do dono.
- `frontend/src/pages/auth/AcessoPinPage.tsx`: tela de acesso operacional por PIN.
- `frontend/src/pages/admin/AdminDashboardPage.tsx`: dashboard protegido do dono.
- `frontend/src/pages/garcom/GarcomDashboardPage.tsx`: terminal protegido do garçom.
- `frontend/src/pages/cozinha/CozinhaKdsPage.tsx`: kds protegido da cozinha em Dark Mode.
- `frontend/src/pages/DesignSystemPage.tsx`: catálogo da fundação de UI preservado.
- `frontend/src/pages/NotFoundPage.tsx`: tela 404 padronizada.
- `frontend/src/App.tsx`: árvore de roteamento e AuthProvider.
- `auditoria/0023-roteamento-cliente-http-auth-context.md`: registro desta auditoria.
- `auditoria/indice.md`: índice atualizado.

---

## 4. Validação e Qualidade

- **Compilação TypeScript / Vite**: `npm run build` executado com zero erros de tipagem.
- **Testes Backend**: 65/65 testes automatizados aprovados no `pytest`.
- **Zero Emojis**: Rigorosamente respeitado em toda a interface e mensagens.
- **Docker Compose**: Container frontend atualizado e pronto para navegação em `http://localhost:5173`.
