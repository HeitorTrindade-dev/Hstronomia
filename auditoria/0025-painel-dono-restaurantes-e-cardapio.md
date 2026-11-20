# 0025 — Painel do Dono: Gestão Multi-Restaurante e Cardápio Completo

**Data:** 2026-11-20  
**Autor:** Heitor / Antigravity Agent  
**Issue Relacionada:** [#52 - [Frontend] Painel do Dono: Gestao de Restaurantes e Cardapio Completo](https://github.com/HeitorTrindade-dev/Hstronomia/issues/52)  
**Branch:** `feat/52-painel-restaurantes-cardapio`

---

## 1. Contexto e Motivação

Com os fluxos de autenticação e navegação finalizados (Issues #49, #50 e #51), a Issue #52 implementa o coração da administração do negócio para o Dono do restaurante:
1. **Gestão de Restaurantes**: Criação de estabelecimentos, chaveamento de contexto multi-tenant ativo no topo da aplicação, edição de dados públicos (nome e slug) e rotação segura de PINs de salão e cozinha.
2. **Gestão do Cardápio**: Tabela densa de produtos, filtros em tempo real, cadastro e edição de pratos/bebidas, pausa de disponibilidade no salão (mutação otimista) e desativação segura via soft-delete para garantir a imutabilidade do histórico financeiro de vendas já realizadas.

---

## 2. Implementações Realizadas

### 2.1. Serviços e Tipos
- [cardapio.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/types/cardapio.ts): Definição de `Item`, `ItemCreateInput`, `ItemUpdateInput`.
- [cardapio.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/services/cardapio.ts): Métodos tipados para `listarItens`, `criarItem`, `atualizarItem`, `alterarDisponibilidade`, `desativarItem` e `reativarItem`.
- [restaurante.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/types/restaurante.ts): Definição expandida de `Restaurante`, `RestauranteCreateInput`, `RestauranteUpdateInput` e `RestaurantePinsUpdateInput`.
- [restaurante.ts](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/services/restaurante.ts): Métodos tipados para `listarMeusRestaurantes`, `criarRestaurante`, `atualizarRestaurante` e `atualizarPins`.

### 2.2. Gestão de Restaurantes & Rotação de PINs ([Restaurantes.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/admin/Restaurantes.tsx))
- Listagem dos estabelecimentos do gestor autenticado com identificador visual do restaurante ativo (`Badge variant="emerald" withDot`).
- Ação para selecionar/trocar restaurante ativo, persistindo no contexto global e `localStorage`.
- [RestauranteModal.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/components/restaurante/RestauranteModal.tsx): Criação e edição com validação Zod (slug padronizado e PINs iniciais distintos de 4 a 20 dígitos).
- [PinsModal.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/components/restaurante/PinsModal.tsx): Rotação segura dos PINs operacionais de Garçom e Cozinha com aviso de segurança.

### 2.3. Gestão do Cardápio ([Cardapio.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/admin/Cardapio.tsx))
- **Tabela Densa e Acessível**: Colunas estruturadas para Nome & Descrição, Preço formatado em Reais (`tabular-nums`), Status com Semáforo Operacional e Ações.
- **Filtros Ágeis**: Busca por texto (nome ou ingredientes), filtro toggle de "Apenas disponíveis" e checkbox para "Exibir inativos (desativados)".
- **Mutação Otimista de Disponibilidade**: Pausa e retomada imediata de itens com reversão automática caso ocorra falha de rede.
- **Soft-Delete Seguro**: Modal de confirmação explicando a preservação do histórico de vendas antes de desativar.
- **Reativação de Itens**: Permite reativar pratos previamente desativados sem perda de integridade.
- [ItemModal.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/components/cardapio/ItemModal.tsx): Criação e edição de itens com validação de preço estritamente positivo e campos tipados.
- Skeletons de linhas de tabela para prevenir Cumulative Layout Shift (CLS).

### 2.4. Integração no Layout Universal e Roteamento
- [TopBar.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/components/layout/TopBar.tsx): Seletor dropdown integrado de troca rápida de restaurante ativo e menu de links do Dono (`Visão Geral`, `Cardápio`, `Restaurantes & PINs`).
- [AdminDashboardPage.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/pages/admin/AdminDashboardPage.tsx): Atalhos diretos para os módulos.
- [App.tsx](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/frontend/src/App.tsx): Rotas `/admin/cardapio` e `/admin/restaurantes` protegidas com `allowedRoles={['dono']}`.

---

## 3. Arquivos Criados e Modificados

- `frontend/src/types/cardapio.ts`: tipagem de itens do cardápio.
- `frontend/src/types/restaurante.ts`: tipagem expandida de restaurantes e PINs.
- `frontend/src/services/cardapio.ts`: cliente da API de cardápio.
- `frontend/src/services/restaurante.ts`: cliente da API de restaurantes.
- `frontend/src/components/cardapio/ItemModal.tsx`: modal de criação e edição de pratos.
- `frontend/src/components/restaurante/RestauranteModal.tsx`: modal de criação e edição de estabelecimento.
- `frontend/src/components/restaurante/PinsModal.tsx`: modal de rotação de PINs.
- `frontend/src/components/layout/TopBar.tsx`: seletor de restaurante ativo e links administrativos.
- `frontend/src/pages/admin/Restaurantes.tsx`: página de gestão de estabelecimentos e PINs.
- `frontend/src/pages/admin/Cardapio.tsx`: página de gestão tabular do cardápio.
- `frontend/src/pages/admin/AdminDashboardPage.tsx`: painel inicial com atalhos.
- `frontend/src/App.tsx`: rotas atualizadas.
- `auditoria/0025-painel-dono-restaurantes-e-cardapio.md`: registro desta auditoria.
- `auditoria/indice.md`: índice atualizado.

---

## 4. Validação e Qualidade

- **TypeScript / Vite**: `npm run build` executado com zero erros de compilação.
- **Backend Tests**: 65/65 testes aprovados no `pytest`.
- **Zero Emojis**: 100% respeitado.
- **Docker Compose**: Container frontend atualizado e pronto para testes locais.
