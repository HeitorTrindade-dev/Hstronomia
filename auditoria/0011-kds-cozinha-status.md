# 0011 — Endpoints e Fluxo de Status da Cozinha (KDS)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Cozinha (KDS) / Segurança
- **Issue Vinculada**: [#16](https://github.com/HeitorTrindade-dev/Hstronomia/issues/16)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #16: disponibilizar a fila de pedidos em tempo real para a equipe da cozinha (`GET /api/v1/cozinha/pedidos`) e o fluxo de atualização de status (`PATCH /api/v1/cozinha/pedidos/{item_comanda_id}/status`) com máquina de estados estrita (`pendente -> em_preparo -> pronto -> entregue`), isolamento multi-tenant e controle de acesso por função (RBAC).

---

## 2. Decisões Técnicas Tomadas

1. **RBAC para Cozinha e Dono (`backend/src/controllers/deps.py`)**:
   - Preservadas intactas `get_current_cozinha` e `get_current_garcom` para compatibilidade com a suíte existente.
   - Adicionadas `get_current_cozinha_ou_dono` e `get_cozinha_restaurante_id`, permitindo acesso às roles `"cozinha"` e `"dono"` e bloqueando `"garcom"` com HTTP `403`. Para `"dono"`, a resolução reutiliza `_resolver_restaurante_do_dono`; para `"cozinha"`, valida o `restaurante_id` da sessão operacional contra eventual query param.

2. **Schemas KDS e Minimização de Dados (`backend/src/schemas/cozinha.py`)**:
   - Criado `CozinhaPedidoStatusUpdate` com `ConfigDict(extra="forbid")` (OWASP A03) e `StatusItemCozinha = Literal["pendente", "em_preparo", "pronto", "entregue"]`.
   - Criado `CozinhaPedidoResponse` expondo exclusivamente dados operacionais do pedido (`id`, `comanda_id`, `item_id`, `nome_item`, `quantidade`, `observacao`, `status`, `criado_em`) e contexto da comanda (`numero_mesa`, `identificador`, `tipo_atendimento`), omitindo valores monetários (OWASP API3).

3. **Repositório Multi-tenant com Eager-Loading (`backend/src/repositories/item_comanda.py`)**:
   - Estendidos `get_by_id_and_restaurante` e `update_status` com o parâmetro keyword-only opcional `carregar_comanda: bool = False` (aplicando `selectinload(ItemComanda.comanda)` quando `True`) para evitar `MissingGreenlet` em contexto assíncrono.
   - Adicionado critério determinístico de desempate `ItemComanda.id.asc()` após `ItemComanda.criado_em.asc()` em `list_por_status_cozinha`.

4. **Máquina de Estados e Serviço KDS (`backend/src/services/cozinha.py` e `backend/src/controllers/v1/cozinha.py`)**:
   - `listar_pedidos`: lista itens em `("pendente", "em_preparo")` (ou filtrados via `?status=`) apenas de comandas com `status == "aberta"` do restaurante autenticado, ordenados em FIFO e com paginação limitada (`1 <= limit <= 100`, `offset >= 0`).
   - `atualizar_status_pedido`: valida existência e posse por `restaurante_id` (`404` contra IDOR), bloqueia alterações em comandas fechadas/canceladas (`400`), impõe transições sequenciais estritas `pendente -> em_preparo -> pronto -> entregue` (`400` para pulos, retrocessos, no-ops e estado terminal `entregue`), registra log de auditoria capturando `status_anterior` antes da mutação e confirma transação no controller.
   - Router montado em `backend/src/main.py` sob `/api/v1`.

5. **Testes Automatizados (`backend/tests/test_cozinha_kds.py`)**:
   - Cobertura completa de ordenação FIFO, contexto da comanda, filtros `?status=`, paginação limitada, exclusão de itens `pronto`/`entregue`/comandas fechadas ou canceladas, máquina de estados estrita, RBAC (`cozinha` e `dono` permitidos, `garcom` bloqueado), múltiplos restaurantes do dono, bloqueio de IDOR cross-tenant e `extra="forbid"`.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Adição de `get_current_cozinha_ou_dono` e `get_cozinha_restaurante_id` (e ajuste de anotações de tipo).
- [`backend/src/repositories/item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item_comanda.py): Parâmetro opcional `carregar_comanda` em `get_by_id_and_restaurante`/`update_status` e ordenação determinística em `list_por_status_cozinha`.
- [`backend/src/schemas/cozinha.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/cozinha.py): Schemas Pydantic v2 do KDS.
- [`backend/src/services/cozinha.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/cozinha.py): `CozinhaService` com máquina de estados e regras KDS.
- [`backend/src/controllers/v1/cozinha.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/cozinha.py): Endpoints `GET /api/v1/cozinha/pedidos` e `PATCH /api/v1/cozinha/pedidos/{item_comanda_id}/status`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Registro do `cozinha_router` em `/api/v1`.
- [`backend/tests/test_cozinha_kds.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_cozinha_kds.py): Testes automatizados da Issue #16.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0011.
