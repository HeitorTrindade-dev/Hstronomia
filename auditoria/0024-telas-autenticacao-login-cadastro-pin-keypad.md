# 0024 — Telas de Autenticação: Login, Cadastro e Terminal por PIN com Keypad Touch

**Data:** 2026-11-20  
**Autor:** Heitor / Antigravity Agent  
**Issue Relacionada:** [#51 - [Frontend] Telas de Autenticacao: Login/Cadastro do Dono e Acesso Operacional por PIN](https://github.com/HeitorTrindade-dev/Hstronomia/issues/51)  
**Branch:** `feat/51-telas-login-pin`

---

## 1. Contexto e Motivação

Com a fundação visual e a infraestrutura de rotas e cliente HTTP estabelecidas (Issues #49 e #50), a Issue #51 implementa a camada de entrada visual no sistema:
- **Painel do Dono**: Telas de Login e Cadastro com validação de formulários via React Hook Form e Zod, tratando tentativas excessivas e bloqueios por rate limit (HTTP 429).
- **Terminal Operacional (Garçom / Cozinha)**: Acesso veloz através de slug do restaurante e PIN numérico, utilizando um Teclado Virtual Numérico (PinKeypad) touch-friendly com área de toque mínima de 44px (padrão WCAG), otimizado para celulares e tablets de operação.

---

## 2. Implementações Realizadas

### 2.1. Componente Teclado Virtual Numérico (`frontend/src/components/auth/PinKeypad.tsx`)
- Grade 3x3 com dígitos 0 a 9, botão de Apagar/Backspace (`Delete`) e botão de Confirmação rápida (`Check`).
- **Área de Toque Otimizada**: Botões de 56px de altura (`h-14`), superando com folga os 44px mínimos exigidos para acessibilidade e uso ágil com uma mão em ambiente de salão/cozinha.
- **Feedback Visual de Dígitos**: Indicadores circulares animados que preenchem à medida que o PIN é digitado.
- **Suporte Híbrido**: Captura eventos tanto de cliques touch nos botões visuais quanto teclas físicas do teclado (números, Backspace, Enter e Escape).
- **Zero Emojis**: Ícones exclusivos do `lucide-react` com `strokeWidth={2}`.

### 2.2. Login do Dono (`frontend/src/pages/auth/LoginDono.tsx`)
- Formulário validado com React Hook Form e Zod (`z.object({ email: z.string().email(), senha: z.string().min(1) })`).
- Acessibilidade semântica com `autoComplete="username"`, `autoComplete="current-password"`, `spellcheck="false"`.
- **Tratamento de Rate Limit (HTTP 429)**: Leitura do header `Retry-After` com bloqueio visual temporário e contagem regressiva em segundos (`tabular-nums font-mono`).
- Redirecionamento automático para `/admin` após autenticação.

### 2.3. Cadastro do Dono (`frontend/src/pages/auth/CadastroDono.tsx`)
- Formulário com campos `nome`, `email`, `senha` e `confirmacaoSenha`.
- Validação refinada no Zod (`refine`) para garantia de correspondência das senhas digitadas.
- Feedback visual de sucesso e tratamento de erros de unicidade de email e 429.
- Redirecionamento automático para a tela de login após cadastro.

### 2.4. Acesso Operacional por PIN (`frontend/src/pages/auth/AcessoOperacional.tsx`)
- Rota parametrizada `/acesso/:slug`.
- Consumo assíncrono dos dados públicos do restaurante via `restauranteService.obterPorSlug(slug)`.
- **Prevenção de Layout Shift**: Skeletons exibidos enquanto os dados do restaurante são consultados.
- Seletor de função pretendida (Garçom ou Cozinha) com badges informativos de semáforo operacional.
- Integração completa com o `PinKeypad`.
- Redirecionamento imediato para `/garcom` ou `/cozinha` após validação do PIN.

### 2.5. Serviços e Tipos
- [restaurante.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/services/restaurante.ts): Cliente para `GET /api/v1/restaurantes/slug/:slug`.
- [restaurante.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/types/restaurante.ts): Tipo `RestaurantePublico`.

---

## 3. Arquivos Criados e Modificados

- `frontend/package.json`: adição de `react-hook-form`, `zod` e `@hookform/resolvers`.
- `frontend/src/types/restaurante.ts`: interface pública de restaurante.
- `frontend/src/services/restaurante.ts`: serviço de consulta pública de restaurante.
- `frontend/src/components/auth/PinKeypad.tsx`: teclado virtual numérico touch-friendly.
- `frontend/src/pages/auth/LoginDono.tsx`: tela de login do dono com Zod e 429.
- `frontend/src/pages/auth/CadastroDono.tsx`: tela de cadastro do dono com confirmação de senha.
- `frontend/src/pages/auth/AcessoOperacional.tsx`: terminal por PIN com skeletons e keypad.
- `frontend/src/App.tsx`: rotas atualizadas com os novos componentes oficiais.
- `auditoria/0024-telas-autenticacao-login-cadastro-pin-keypad.md`: registro desta auditoria.
- `auditoria/indice.md`: índice atualizado.

---

## 4. Validação e Qualidade

- **TypeScript / Vite**: `npm run build` aprovado sem erros de compilação.
- **Backend Tests**: 65/65 testes aprovados no `pytest`.
- **Zero Emojis**: 100% respeitado.
- **Docker Compose**: Container frontend atualizado e pronto para testes locais.
