# 0019 — Consolidação de Segurança OWASP, Correções de Bugs, Gestão de Itens da Comanda e Melhorias Gerais

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Segurança / Comandas / Cardápio / Financeiro / Qualidade
- **Issue Vinculada**: [#45](https://github.com/HeitorTrindade-dev/Hstronomia/issues/45)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #45 para consolidar todas as correções de bugs, endurecimentos de segurança OWASP, funcionalidades operacionais pendentes de comandas/cardápio e melhorias de performance e lint antes do início do desenvolvimento do frontend.

---

## 2. Decisões Técnicas Tomadas

1. **Correções de Bugs e Integridade (`auth.py`, `comanda.py`, `test_financeiro.py`)**:
   - `AuthService.cadastrar_dono` passa a capturar `IntegrityError` em cadastros concorrentes (TOCTOU) com `session.rollback()` e retorno `400 Bad Request` (`"E-mail já cadastrado no sistema."`).
   - `ComandaService.fechar_comanda` bloqueia o fechamento de comandas sem itens lançados (`400 Bad Request`), orientando o uso do cancelamento.
   - `test_alembic_migration_0004_estrutura_e_cadeia` atualizado para validar a revisão `0004_criar_tabela_despesa` e o encadeamento até o head atual (`0005_indice_unico_mesa_aberta`).

2. **Hardening de Segurança OWASP (`config.py`, `security.py`, `rate_limit.py`, `deps.py`, `schemas/`, `restaurante.py`)**:
   - Limite estrito de 72 bytes UTF-8 e bloqueio de null bytes (`\x00`) em `senha` nos schemas `DonoCreate` e `LoginRequest` e nas funções `hash_password` / `verify_password` (tratando `ValueError` com segurança).
   - Rejeição de null bytes (`\x00`) nos schemas `ItemCreate`, `ItemUpdate`, `DespesaCreate` e `DespesaUpdate`.
   - Obrigatoriedade da claim `pin_fp` para sessões operacionais (`garcom` e `cozinha`) em `get_current_user` (`deps.py`) e criação do helper `create_operational_token`.
   - Controle de limite máximo de chaves (`max_keys` configurável via `OPERATIONAL_RATE_LIMIT_MAX_KEYS`) e poda de chaves expiradas/antigas em `SlidingWindowRateLimiter` contra exaustão de memória (OWASP API4).
   - Bloqueio de `list_all` e `delete_by_id` sem escopo de `dono_id` em `RestauranteRepository`.

3. **Novas Funcionalidades Operacionais (`comanda.py`, `item_comanda.py`, `item.py`)**:
   - `PATCH /api/v1/comandas/{comanda_id}/itens/{item_comanda_id}`: permite que Garçom ou Dono atualizem `quantidade` e/ou `observacao` de item `pendente` em comanda `aberta`, mantendo `nome_item` e `preco_unitario` congelados e recalculando `subtotal` e `valor_total`.
   - `DELETE /api/v1/comandas/{comanda_id}/itens/{item_comanda_id}`: permite remover item `pendente` de comanda `aberta` e recalcular `subtotal` e `valor_total`.
   - `PATCH /api/v1/itens/{item_id}/reativar`: permite ao Dono reativar (`ativo = True`) um item do cardápio previamente desativado via soft-delete.

4. **Performance, Configurações e Qualidade de Código (`config.py`, `.env.example`, `financeiro.py`, `conftest.py`)**:
   - Adicionados `BCRYPT_ROUNDS` (default `12`, mínimo `12` em produção; `4` nos testes via `conftest.py`, reduzindo o tempo da suíte de ~226s para ~40s) e `APP_TIMEZONE` (default `"UTC"`, validado via `ZoneInfo` e aplicado na janela de datas de `FinanceiroService.obter_resumo`).
   - Padronização completa de imports e tipagens modernas em `backend/src/`, `backend/alembic/` e `backend/tests/` com `ruff check .` passando com 0 erros.

---

## 3. Arquivos Criados / Modificados
- [`backend/.env.example`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/.env.example) e [`backend/src/core/config.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/config.py): `APP_TIMEZONE`, `BCRYPT_ROUNDS` e `OPERATIONAL_RATE_LIMIT_MAX_KEYS`.
- [`backend/src/core/security.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/security.py): Validação de 72 bytes/null bytes no Bcrypt e `create_operational_token`.
- [`backend/src/core/rate_limit.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/rate_limit.py): Limite `max_keys` e eviction de chaves expiradas/antigas.
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Obrigatoriedade de `pin_fp` em sessões operacionais.
- [`backend/src/schemas/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/auth.py), [`backend/src/schemas/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/item.py), [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py), [`backend/src/schemas/financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/financeiro.py): Validações contra null bytes, limite de 72 bytes em senha, `ItemComandaUpdate` e `ItemReativarRequest`.
- [`backend/src/repositories/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/restaurante.py), [`backend/src/repositories/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item.py), [`backend/src/repositories/item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item_comanda.py): Blindagem de `RestauranteRepository`, método `reativar` em `ItemRepository` e `delete_by_id_and_restaurante` em `ItemComandaRepository`.
- [`backend/src/services/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/auth.py), [`backend/src/services/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/item.py), [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py), [`backend/src/services/financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/financeiro.py): Tratamento de `IntegrityError` no cadastro de Dono, reativação de item, edição/remoção de item de comanda, bloqueio de fechamento de comanda vazia e suporte a `APP_TIMEZONE`.
- [`backend/src/controllers/v1/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/item.py) e [`backend/src/controllers/v1/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/comanda.py): Endpoints `PATCH /api/v1/itens/{id}/reativar`, `PATCH /api/v1/comandas/{id}/itens/{item_comanda_id}` e `DELETE /api/v1/comandas/{id}/itens/{item_comanda_id}`.
- [`backend/tests/test_consolidacao_backend.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_consolidacao_backend.py) e demais arquivos em `backend/tests/`: Testes automatizados da Issue #45 e padronização `ruff`.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0019.
