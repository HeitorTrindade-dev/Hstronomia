# 0018 — Blindagem Multi-Tenant no BaseRepository contra IDOR Acidental

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Database / Segurança
- **Issue Vinculada**: [#39](https://github.com/HeitorTrindade-dev/Hstronomia/issues/39)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #39: blindar a camada de persistência para que repositórios de entidades operacionais multi-tenant (`ItemRepository`, `ComandaRepository`, `ItemComandaRepository` e `DespesaRepository`) não exponham métodos herdados sem filtro de `restaurante_id` (`get_by_id`, `get_by`, `list_by`, `list_all`, `delete_by_id`), eliminando o risco de IDOR acidental e proibindo exclusão física de `Item`.

---

## 2. Decisões Técnicas Tomadas

1. **`TenantBaseRepository` e `TenantIsolationError` (`backend/src/repositories/base.py`)**:
   - Criada a exceção `TenantIsolationError(PermissionError, NotImplementedError)`.
   - Criada a classe `TenantBaseRepository(BaseRepository[ModelType])` que sobrescreve e bloqueia explicitamente `get_by_id`, `get_by`, `list_by`, `list_all` e `delete_by_id`, exigindo que qualquer leitura ou mutação utilize os métodos tipados com `restaurante_id`.

2. **Migração dos Repositórios Operacionais (`item.py`, `comanda.py`, `item_comanda.py`, `despesa.py`)**:
   - `ItemRepository`, `ComandaRepository`, `ItemComandaRepository` e `DespesaRepository` passam a herdar de `TenantBaseRepository`.
   - `ItemRepository.delete_by_id` reforça a proibição de `DELETE` físico de itens do cardápio (Regra Global #2), direcionando para `soft_delete(item_id, restaurante_id)`.

3. **Testes Automatizados (`backend/tests/test_tenant_repository_guard.py`)**:
   - Validação unitária de que todos os 4 repositórios operacionais herdam de `TenantBaseRepository` e lançam `TenantIsolationError` ao chamar qualquer método sem `restaurante_id`.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/repositories/base.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/base.py): `TenantBaseRepository` e `TenantIsolationError`.
- [`backend/src/repositories/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item.py): Herança de `TenantBaseRepository` e bloqueio de delete físico.
- [`backend/src/repositories/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/comanda.py): Herança de `TenantBaseRepository`.
- [`backend/src/repositories/item_comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item_comanda.py): Herança de `TenantBaseRepository`.
- [`backend/src/repositories/despesa.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/despesa.py): Herança de `TenantBaseRepository`.
- [`backend/src/repositories/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/__init__.py): Exportação de `TenantBaseRepository` e `TenantIsolationError`.
- [`backend/tests/test_tenant_repository_guard.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_tenant_repository_guard.py): Testes automatizados da Issue #39.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0018.
