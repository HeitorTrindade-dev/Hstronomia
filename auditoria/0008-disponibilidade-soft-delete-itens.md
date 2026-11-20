# 0008 — Controle de Disponibilidade e Soft-Delete de Itens

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Cardápio / Segurança
- **Issue Vinculada**: [#10](https://github.com/HeitorTrindade-dev/Hstronomia/issues/10)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #10: permitir que o Dono pause/retome a disponibilidade de itens esgotados no dia e desative itens via soft-delete (`ativo = False`) preservando a imutabilidade histórica de vendas, garantindo que consultas do Garçom exibam exclusivamente itens ativos e disponíveis.

---

## 2. Decisões Técnicas Tomadas

1. **Schema de Disponibilidade (`backend/src/schemas/item.py`)**:
   - Criado `ItemDisponibilidadeUpdate` com `extra="forbid"` (OWASP A03), aceitando exclusivamente o campo booleano `disponivel`.

2. **Repositório (`backend/src/repositories/item.py`)**:
   - Adicionado `update_disponibilidade(item_id, restaurante_id, disponivel)` com filtro obrigatório por `restaurante_id`.
   - Adicionado `soft_delete(item_id, restaurante_id)` atualizando `ativo = False` e `disponivel = False` sem `DELETE` físico, preservando integridade referencial e histórico de vendas.
   - Adicionado `list_disponiveis_para_garcom(restaurante_id)` filtrando estritamente `ativo == True` e `disponivel == True`.

3. **Regras de Negócio (`backend/src/services/item.py`)**:
   - `alterar_disponibilidade`: bloqueia alteração de disponibilidade em itens já desativados (`400 Bad Request`) e retorna `404` caso não exista no restaurante autenticado.
   - `desativar_item`: aplica soft-delete e registra log de auditoria da desativação.

4. **Endpoints e Filtro Estrito do Garçom (`backend/src/controllers/v1/item.py`)**:
   - `PATCH /api/v1/itens/{item_id}/disponibilidade` (restrito ao Dono via `get_dono_restaurante_id`, bloqueando Garçom/Cozinha com `403`).
   - `DELETE /api/v1/itens/{item_id}` (restrito ao Dono via `get_dono_restaurante_id`, retornando `200 OK` com o item desativado).
   - `GET /api/v1/itens`: quando `current_user.role == "garcom"`, força `incluir_inativos=False` e `apenas_disponiveis=True` independentemente dos query params enviados pelo cliente.

5. **Testes Automatizados (`backend/tests/test_item.py`)**:
   - Cobertura de pausa/retomada de disponibilidade, validação `extra="forbid"`, soft-delete sem remoção física do banco, bloqueio de edição de disponibilidade de item inativo, RBAC/BFLA, IDOR cross-tenant e filtro estrito do Garçom.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/schemas/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/item.py): DTO `ItemDisponibilidadeUpdate`.
- [`backend/src/repositories/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/item.py): Métodos `update_disponibilidade`, `soft_delete` e `list_disponiveis_para_garcom`.
- [`backend/src/services/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/item.py): Métodos `alterar_disponibilidade` e `desativar_item`.
- [`backend/src/controllers/v1/item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/item.py): Endpoints `PATCH /api/v1/itens/{id}/disponibilidade`, `DELETE /api/v1/itens/{id}` e filtro obrigatório para o Garçom em `GET /api/v1/itens`.
- [`backend/tests/test_item.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_item.py): Testes de disponibilidade, soft-delete e filtro estrito do Garçom.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0008.
