# 0020 — Refinamento de Segurança OWASP, Edição de Restaurante/Comanda e Validações de Schemas

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Segurança / Restaurantes / Comandas / Cardápio
- **Issue Vinculada**: [#47](https://github.com/HeitorTrindade-dev/Hstronomia/issues/47)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #47 com os refinamentos identificados na segunda vistoria geral do backend: rollback explícito em `IntegrityError` na criação de restaurante, validação estrita de `ItemUpdate` contra payloads vazios ou campos obrigatórios nulos, ocultação da documentação OpenAPI/Swagger em produção (`DEBUG=False`), blindagem de `DonoRepository` contra listagem global e exclusão em cascata, e disponibilização dos endpoints de edição de dados do restaurante (`PATCH /api/v1/restaurantes/{id}`) e edição/troca de mesa da comanda (`PATCH /api/v1/comandas/{id}`).

---

## 2. Decisões Técnicas Tomadas

1. **Correções e Hardening OWASP (`main.py`, `dono.py`, `item.py`, `restaurante.py`)**:
   - `docs_url`, `redoc_url` e `openapi_url` em `backend/src/main.py` ficam habilitados somente quando `settings.DEBUG` é `True`, evitando exposição pública de schemas em produção (OWASP API8).
   - `DonoRepository` (`backend/src/repositories/dono.py`) bloqueia `list_all` e `delete_by_id` com `TenantIsolationError`.
   - `ItemUpdate` (`backend/src/schemas/item.py`) exige ao menos um campo informado e rejeita `None` explícito em `nome`, `preco` e `disponivel`.
   - `RestauranteService.criar_restaurante` executa `await self.session.rollback()` ao capturar `IntegrityError` concorrente.

2. **Edição de Dados do Restaurante (`PATCH /api/v1/restaurantes/{restaurante_id}`)**:
   - Criado `RestauranteUpdate` (`nome` e/ou `slug` opcionais, não nulos, com validação de formato de slug e `extra="forbid"`).
   - `RestauranteRepository.update_dados` e `RestauranteService.atualizar_restaurante` validam propriedade (`dono_id`), unicidade de `slug` (`409 Conflict`) e tratam `IntegrityError` concorrente com rollback.

3. **Edição e Troca de Mesa de Comanda (`PATCH /api/v1/comandas/{comanda_id}`)**:
   - Criado `ComandaUpdate` (`numero_mesa`, `identificador` e/ou `tipo_atendimento` com `extra="forbid"`).
   - `ComandaRepository.update_atendimento` e `ComandaService.atualizar_comanda` permitem alterar mesa, identificador ou modalidade de comandas `abertas`, validando consistência cruzada (`mesa` exige `numero_mesa`; `balcao`/`viagem` exigem `numero_mesa=None`) e conflito de mesa ocupada (`409 Conflict`).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Condicionamento de `docs_url`, `redoc_url` e `openapi_url` a `settings.DEBUG`.
- [`backend/src/repositories/dono.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/dono.py): Bloqueio de `list_all` e `delete_by_id` com `TenantIsolationError`.
- [`backend/src/schemas/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/item.py): `@model_validator` em `ItemUpdate`.
- [`backend/src/schemas/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/restaurante.py), [`backend/src/repositories/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/restaurante.py), [`backend/src/services/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/restaurante.py), [`backend/src/controllers/v1/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/restaurante.py): Rollback em `IntegrityError` e endpoint `PATCH /api/v1/restaurantes/{restaurante_id}`.
- [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py), [`backend/src/repositories/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/comanda.py), [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py), [`backend/src/controllers/v1/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/comanda.py): Endpoint `PATCH /api/v1/comandas/{comanda_id}` para troca de mesa e edição de atendimento.
- [`backend/tests/test_dono_restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_dono_restaurante.py) e [`backend/tests/test_consolidacao_backend.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_consolidacao_backend.py): Testes automatizados da Issue #47.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0020.
