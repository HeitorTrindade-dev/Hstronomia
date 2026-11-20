# 0009 — Models e Repositories de Comanda e ItemComanda

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Database / Comandas
- **Issue Vinculada**: [#12](https://github.com/HeitorTrindade-dev/Hstronomia/issues/12)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #12: modelagem e persistência das entidades centrais de atendimento (`Comanda` e `ItemComanda`), fornecendo a base multi-tenant e de imutabilidade histórica que desbloqueia os módulos de Pedidos (#13), Cozinha KDS (#16), Fechamento (#18) e Financeiro (#20).

---

## 2. Decisões Técnicas Tomadas

1. **Models SQLAlchemy (`backend/src/models/comanda.py`, `backend/src/models/item_comanda.py`)**:
   - `Comanda`: colunas conforme [schema.dbml](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/schema.dbml) (`numero_mesa`, `identificador`, `tipo_atendimento`, `status`, `subtotal`, `taxa_servico`, `desconto`, `valor_total` em `Numeric(10, 2)` / `Decimal`, `metodo_pagamento`, `criado_em`, `fechado_em`), índices compostos `ix_comanda_restaurante_status` e `ix_comanda_restaurante_mesa_status`.
   - `ItemComanda`: colunas de congelamento histórico (`nome_item`, `preco_unitario` em `Numeric(10, 2)`), `quantidade`, `observacao`, `status` (default `'pendente'`), FK `comanda_id` (`ON DELETE CASCADE`) e FK `item_id` (`ON DELETE RESTRICT` para proteger o histórico contábil contra exclusões físicas).

2. **Migração Alembic (`backend/alembic/versions/0003_criar_tabelas_comanda_e_item_comanda.py`)**:
   - Revisão `0003_comanda_item_comanda` encadeada em `0002_criar_tabela_item`, com DDL PostgreSQL validada via `alembic upgrade head --sql`.

3. **Repositórios Multi-tenant (`backend/src/repositories/comanda.py`, `backend/src/repositories/item_comanda.py`)**:
   - `ComandaRepository`: isolamento obrigatório por `restaurante_id` em `get_by_id_and_restaurante` (com `selectinload` opcional de `itens`), `get_aberta_por_mesa`, `list_abertas` (com filtro por `tipo_atendimento`), `list_by_restaurante`, `create`, `update_totais`, `fechar` e `somar_vendas_fechadas_periodo`.
   - `ItemComandaRepository`: isolamento multi-tenant via `JOIN Comanda` filtrando `Comanda.restaurante_id == restaurante_id` em `get_by_id_and_restaurante`, `list_by_comanda`, `list_por_status_cozinha` (KDS com `selectinload(ItemComanda.comanda)`), `create` (validando posse da comanda), `update_status` e `update_item` (sem alterar campos congelados).

4. **Testes Automatizados (`backend/tests/test_comanda_repository.py`)**:
   - Cobertura de busca de comandas abertas por mesa/balcão, fechamento, consolidação financeira por período, congelamento histórico de `nome_item`/`preco_unitario`, fila KDS e bloqueio de IDOR cross-tenant em ambos os repositórios.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/models/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/comanda.py): Model `Comanda`.
- [`backend/src/models/item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/item_comanda.py): Model `ItemComanda`.
- [`backend/src/models/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/restaurante.py): Relacionamento `comandas` em `Restaurante`.
- [`backend/src/models/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/__init__.py): Exportação de `Comanda` e `ItemComanda`.
- [`backend/alembic/versions/0003_criar_tabelas_comanda_e_item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/versions/0003_criar_tabelas_comanda_e_item_comanda.py): Migração Alembic `0003`.
- [`backend/src/repositories/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/comanda.py): Repositório `ComandaRepository`.
- [`backend/src/repositories/item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item_comanda.py): Repositório `ItemComandaRepository`.
- [`backend/src/repositories/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/__init__.py): Exportação dos repositórios.
- [`backend/tests/test_comanda_repository.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_comanda_repository.py): Testes automatizados da Issue #12.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0009.
