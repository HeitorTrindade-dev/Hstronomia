# 0007 — CRUD de Itens do Cardápio

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Database / Cardápio
- **Issue Vinculada**: [#9](https://github.com/HeitorTrindade-dev/Hstronomia/issues/9)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #9: gerenciamento completo de itens/produtos do cardápio (cadastro, listagem paginada e edição com atualização de preço), garantindo isolamento estrito multi-tenant (`restaurante_id`), precisão monetária em `Decimal` e controle de acesso por papel (RBAC).

---

## 2. Decisões Técnicas Tomadas

1. **Modelagem e Migração (`backend/src/models/item.py`, `backend/alembic/versions/0002_criar_tabela_item.py`)**:
   - Criado model `Item` espelhando fielmente o [schema.dbml](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/schema.dbml) (`preco` em `Numeric(10, 2)` / `Decimal`, `disponivel` e `ativo` com default `true`, FK `restaurante_id` com `ON DELETE CASCADE`).
   - Adicionado índice composto `ix_item_restaurante_ativo` em `(restaurante_id, ativo)` para listagens eficientes por tenant.
   - Criada migração Alembic `0002_criar_tabela_item` encadeada sobre `0001_dono_restaurante`, com DDL PostgreSQL validada via `alembic upgrade head --sql`.

2. **Repositório Multi-tenant (`backend/src/repositories/item.py`)**:
   - `ItemRepository` exige `restaurante_id` em todas as consultas e alterações (`get_by_id_and_restaurante`, `list_by_restaurante`, `create`, `update`), bloqueando IDOR/BOLA na camada de dados.

3. **Schemas e Regras de Negócio (`backend/src/schemas/item.py`, `backend/src/services/item.py`)**:
   - `ItemCreate` e `ItemUpdate` com `extra="forbid"` (OWASP A03), preço estritamente em `Decimal > 0.00` (OWASP A04) e normalização de `nome`/`descricao`.
   - `ItemService` normaliza valores monetários para 2 casas decimais (`ROUND_HALF_UP`), impede edição de itens desativados (`ativo=False`) e registra log de auditoria em alterações de preço (OWASP A09).

4. **Resolução Segura de Tenant e Endpoints (`backend/src/controllers/deps.py`, `backend/src/controllers/v1/item.py`)**:
   - Criadas dependências `get_dono_restaurante_id` e `get_sessao_restaurante_id`: resolvem automaticamente o restaurante quando o Dono possui apenas um, exigem `restaurante_id` quando possui múltiplos e bloqueiam com `403 Forbidden` qualquer tentativa de acessar restaurante de terceiros.
   - `GET /api/v1/itens`: acessível para Dono, Garçom e Cozinha com paginação limitada (`limit <= 100`, OWASP A07); apenas o Dono pode usar `incluir_inativos=true`.
   - `POST /api/v1/itens` e `PUT /api/v1/itens/{id}`: restritos exclusivamente ao Dono (`403 Forbidden` para Garçom/Cozinha, OWASP API5 / BFLA).

5. **Testes Automatizados (`backend/tests/test_item.py`)**:
   - Cobertura completa de repositório (isolamento multi-tenant), service (Decimal, reajuste de preço, item inativo), endpoints (CRUD, validação `extra="forbid"`, paginação, RBAC/BFLA, IDOR cross-tenant e dono com múltiplos restaurantes).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/models/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/item.py): Entidade SQLAlchemy `Item`.
- [`backend/src/models/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/restaurante.py): Relacionamento `itens` em `Restaurante`.
- [`backend/src/models/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/__init__.py): Exportação de `Item`.
- [`backend/alembic/versions/0002_criar_tabela_item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/versions/0002_criar_tabela_item.py): Migração da tabela `item`.
- [`backend/src/repositories/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item.py): Repositório `ItemRepository`.
- [`backend/src/repositories/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/__init__.py): Exportação de `ItemRepository`.
- [`backend/src/schemas/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/item.py): DTOs `ItemCreate`, `ItemUpdate` e `ItemResponse`.
- [`backend/src/services/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/item.py): Regras de negócio em `ItemService`.
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Dependências `get_dono_restaurante_id` e `get_sessao_restaurante_id`.
- [`backend/src/controllers/v1/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/item.py): Rotas `GET`, `POST` e `PUT` de `/api/v1/itens`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Registro do router de itens.
- [`backend/tests/test_item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_item.py): Testes automatizados da Issue #9.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0007.
