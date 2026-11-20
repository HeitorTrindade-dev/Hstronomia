# 0012 — Módulo Financeiro (Despesas e Fluxo de Caixa)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Database / Financeiro
- **Issue Vinculada**: [#20](https://github.com/HeitorTrindade-dev/Hstronomia/issues/20)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #20: criação do módulo financeiro para registro e gerenciamento de despesas operacionais por restaurante e consolidação do fluxo de caixa (vendas fechadas vs despesas e saldo líquido em `Decimal`), com isolamento multi-tenant estrito e acesso exclusivo ao perfil Dono.

---

## 2. Decisões Técnicas Tomadas

1. **Model `Despesa` e Migração Alembic `0004` (`backend/src/models/despesa.py`, `backend/alembic/versions/0004_criar_tabela_despesa.py`)**:
   - Model `Despesa` alinhado ao [schema.dbml](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/schema.dbml) (`id`, `restaurante_id` FK `ON DELETE CASCADE`, `descricao`, `categoria`, `valor` em `Numeric(10, 2)` / `Decimal`, `data_pagamento` em `Date`, `criado_em`), com índices `ix_despesa_restaurante_id`, `ix_despesa_restaurante_data` e `ix_despesa_restaurante_categoria`.
   - Relacionamento `despesas` adicionado em `Restaurante` (`cascade="all, delete-orphan"`) e exportação de `Despesa` em `src/models/__init__.py`.
   - Migração `0004_criar_tabela_despesa` encadeada sobre `0003_comanda_item_comanda`, com `upgrade()` e `downgrade()` completos e validados em modo `--sql`.

2. **Repositório Multi-tenant (`backend/src/repositories/despesa.py`)**:
   - `DespesaRepository` filtrando obrigatoriamente por `restaurante_id` em todas as operações (`get_by_id_and_restaurante`, `list_by_restaurante`, `create`, `update`, `delete_by_id_and_restaurante`, `somar_despesas_periodo` e `somar_despesas_por_categoria`), evitando métodos globais sem filtro de tenant e normalizando somas em `Decimal` (`ROUND_HALF_UP`).

3. **Schemas, Service e Endpoints RBAC (`backend/src/schemas/financeiro.py`, `backend/src/services/financeiro.py`, `backend/src/controllers/v1/financeiro.py`)**:
   - DTOs `DespesaCreate` e `DespesaUpdate` com `ConfigDict(extra="forbid")`, validação de `valor > 0` (`max_digits=10, decimal_places=2`), categorias permitidas (`insumos`, `contas_fixas`, `manutencao`, `outros`) e rejeição de `null` explícito ou body vazio no `PATCH`.
   - `FinanceiroService`: valida `data_inicio <= data_fim` (`400 Bad Request`), converte datas de filtro em limites UTC inclusivos (`00:00:00Z` até `23:59:59.999999Z`) ao consultar `ComandaRepository.somar_vendas_fechadas_periodo` e calcula `saldo = total_vendas - total_despesas` em `Decimal` (`ROUND_HALF_UP`).
   - Rotas `/api/v1/financeiro/despesas` (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`) e `GET /api/v1/financeiro/resumo` protegidas exclusivamente por `get_dono_restaurante_id` (bloqueando `garcom` e `cozinha` com `403` e protegendo contra IDOR).

4. **Testes Automatizados (`backend/tests/test_financeiro.py`)**:
   - Cobertura completa do `DespesaRepository`, CRUD completo e filtros/paginação, fluxo de caixa no `/resumo` (incluindo limites diários UTC, saldo negativo e precisão `Decimal`), validações de schema, matriz de RBAC (`garcom`, `cozinha`, não autenticado), proteção IDOR/multi-restaurantes e validação offline da cadeia Alembic `0004`.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/models/despesa.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/despesa.py): Model `Despesa`.
- [`backend/src/models/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/restaurante.py): Relacionamento `despesas` em `Restaurante`.
- [`backend/src/models/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/__init__.py): Exportação de `Despesa`.
- [`backend/alembic/versions/0004_criar_tabela_despesa.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/versions/0004_criar_tabela_despesa.py): Migração Alembic `0004`.
- [`backend/src/repositories/despesa.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/despesa.py): Repositório `DespesaRepository`.
- [`backend/src/repositories/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/__init__.py): Exportação de `DespesaRepository`.
- [`backend/src/schemas/financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/financeiro.py): Schemas Pydantic do módulo financeiro.
- [`backend/src/services/financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/financeiro.py): `FinanceiroService`.
- [`backend/src/controllers/v1/financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/financeiro.py): Endpoints `/api/v1/financeiro/*`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Registro do `financeiro_router` em `/api/v1`.
- [`backend/tests/test_financeiro.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_financeiro.py): Testes automatizados da Issue #20.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0012.
