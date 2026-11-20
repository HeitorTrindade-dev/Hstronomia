# 0010 — Service de Pedidos com Congelamento de Preço

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Comandas / Pedidos / Segurança
- **Issue Vinculada**: [#13](https://github.com/HeitorTrindade-dev/Hstronomia/issues/13)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #13: regras de negócio e endpoints para abertura de comandas e adição de itens garantindo obrigatoriamente a imutabilidade histórica de vendas (`nome_item` e `preco_unitario` congelados a partir do registro original de `Item` no banco de dados), suporte a observações no pedido, recálculo preciso de totais em `Decimal` (`ROUND_HALF_UP`), isolamento multi-tenant e controle de acesso por função (RBAC).

---

## 2. Decisões Técnicas Tomadas

1. **Dependências RBAC de Atendimento (`backend/src/controllers/deps.py`)**:
   - Extraído helper interno `_resolver_restaurante_da_sessao` compartilhado entre `get_sessao_restaurante_id` e a nova dependência `get_atendimento_restaurante_id`.
   - Criada `get_current_atendimento`, permitindo acesso exclusivamente às funções `"garcom"` e `"dono"` e bloqueando `"cozinha"` (e demais perfis) com `HTTP 403`.
   - Preservada retrocompatibilidade total com `get_current_operacional` e `get_sessao_restaurante_id`.

2. **Schemas Pydantic v2 (`backend/src/schemas/comanda.py`)**:
   - `ComandaCreate` (`extra="forbid"`): valida `numero_mesa` com `StrictInt` (`1..9999`, rejeitando booleanos/floats), normaliza `identificador` removendo espaços em branco (`"" -> None`), rejeita null bytes (`\x00`) para segurança UTF-8 no PostgreSQL, restringe `tipo_atendimento` a `"mesa" | "balcao" | "viagem"` e exige ao menos `numero_mesa` ou `identificador`.
   - `ItemComandaCreate` (`extra="forbid"`): aceita apenas `item_id`, `quantidade` (`StrictInt`, `1..999`) e `observacao` opcional (máx. 500 caracteres, normalizada e protegida contra `\x00`), bloqueando mass assignment de `nome_item`, `preco_unitario` e `status`.
   - `ComandaResponse` e `ItemComandaResponse` configurados com `from_attributes=True` usando apenas colunas escalares para evitar lazy-load assíncrono (`MissingGreenlet`).

3. **Service de Comandas e Congelamento (`backend/src/services/comanda.py`)**:
   - `ComandaService.quantizar_moeda`: arredondamento financeiro estrito em `Decimal("0.01")` com `ROUND_HALF_UP` (sem uso de `float`).
   - `abrir_comanda`: verifica duplicidade de comanda aberta na mesma mesa via `ComandaRepository.get_aberta_por_mesa` (`409 Conflict` se já existir) e trata `sqlalchemy.exc.MultipleResultsFound` registrando warning e retornando `409 Conflict` em cenários de corrida concorrente.
   - `adicionar_item`: valida posse e existência da comanda (`404`), status `"aberta"` (`400`), posse e existência do item (`404`), estado `ativo=True` e `disponivel=True` (`400`); congela `nome_item` e `preco_unitario` diretamente do `Item` persistido no banco; recalcula `subtotal` e `valor_total` validando o limite máximo de `Numeric(10, 2)` (`MAX_VALOR_MONETARIO = Decimal("99999999.99")`) antes da persistência do item e da atualização via `ComandaRepository.update_totais` (`400 Bad Request` em caso de overflow).
   - **Recomendação futura de endurecimento em banco (PostgreSQL)**: Em uma migration Alembic dedicada (fora do escopo da Issue #13), recomenda-se criar um índice único parcial no PostgreSQL em `(restaurante_id, numero_mesa) WHERE status = 'aberta' AND numero_mesa IS NOT NULL` para garantir atomicamente a unicidade de comanda aberta por mesa no nível de banco de dados.

4. **Controller e Roteamento (`backend/src/controllers/v1/comanda.py`, `backend/src/main.py`)**:
   - Endpoints `POST /api/v1/comandas` (`201 Created`) e `POST /api/v1/comandas/{comanda_id}/itens` (`201 Created`) protegidos por `get_atendimento_restaurante_id`, com commit transacional explícito no controller e registro do `comanda_router` sob `/api/v1`.

5. **Testes Automatizados (`backend/tests/test_comanda_pedidos.py`)**:
   - Suite cobrindo abertura de comandas (garçom, dono, multi-restaurante, mesa duplicada), adição de itens com `observacao`, prova de congelamento histórico de preço/nome após alteração no cardápio (`PUT /api/v1/itens/{id}`), rejeição de itens indisponíveis/inativos/inexistentes e comandas fechadas/canceladas, IDOR cross-tenant, RBAC (`cozinha` bloqueada com `403`, não autenticado), `extra="forbid"` e precisão `Decimal` com `ROUND_HALF_UP`.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Adição de `get_current_atendimento`, `get_atendimento_restaurante_id` e `_resolver_restaurante_da_sessao`.
- [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py): Schemas `ComandaCreate`, `ComandaResponse`, `ItemComandaCreate` e `ItemComandaResponse`.
- [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py): Service `ComandaService` com congelamento histórico e recálculo em `Decimal`.
- [`backend/src/controllers/v1/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/comanda.py): Endpoints `POST /api/v1/comandas` e `POST /api/v1/comandas/{comanda_id}/itens`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Registro do `comanda_router` em `/api/v1`.
- [`backend/tests/test_comanda_pedidos.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_comanda_pedidos.py): Testes automatizados da Issue #13.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0010.
