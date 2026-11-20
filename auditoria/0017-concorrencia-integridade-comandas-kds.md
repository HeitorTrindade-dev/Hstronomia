# 0017 — Concorrência (Race Conditions) e Regras de Integridade em Comandas e KDS

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Database / Comandas / Cozinha
- **Issue Vinculada**: [#38](https://github.com/HeitorTrindade-dev/Hstronomia/issues/38)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #38: eliminar a condição de corrida (TOCTOU) na abertura concorrente de comandas para a mesma mesa por meio de índice único parcial no banco de dados, garantir consistência cruzada entre `tipo_atendimento` e `numero_mesa`, e habilitar o filtro de pedidos `"pronto"` no KDS bem como a entrega (`pronto -> entregue`) pelo Garçom.

---

## 2. Decisões Técnicas Tomadas

1. **Índice Único Parcial para Mesa Aberta (`backend/src/models/comanda.py`, `backend/alembic/versions/0005_indice_unico_mesa_aberta.py`, `backend/src/services/comanda.py`)**:
   - Criado índice único parcial `uq_comanda_restaurante_mesa_aberta` em `(restaurante_id, numero_mesa) WHERE status = 'aberta' AND numero_mesa IS NOT NULL` (com `postgresql_where` e `sqlite_where`), garantindo no nível do SGBD que jamais existam duas comandas abertas simultaneamente na mesma mesa do mesmo restaurante, sem impedir múltiplos históricos fechados/cancelados daquela mesa.
   - `ComandaService.abrir_comanda` captura `IntegrityError` concorrente, efetua rollback da sessão e retorna `409 Conflict` (`"Já existe uma comanda aberta para esta mesa."`).

2. **Validação Cruzada `tipo_atendimento` vs `numero_mesa` (`backend/src/schemas/comanda.py`)**:
   - Em `ComandaCreate`:
     - Quando `tipo_atendimento == "mesa"`, `numero_mesa` é obrigatório.
     - Quando `tipo_atendimento in ("balcao", "viagem")`, `numero_mesa` deve ser `None` (impedindo bloquear uma mesa física em pedidos de balcão/viagem).

3. **Filtro `"pronto"` no KDS e Entrega pelo Garçom (`backend/src/schemas/cozinha.py`, `backend/src/controllers/v1/cozinha.py`)**:
   - `StatusFilaCozinha` expandido para `Literal["pendente", "em_preparo", "pronto"]` (mantendo o default sem query param em `("pendente", "em_preparo")`).
   - `PATCH /api/v1/cozinha/pedidos/{id}/status` permite que o Garçom (`role == "garcom"`) execute exclusivamente a transição para `"entregue"`, mantendo `403 Forbidden` caso o Garçom tente alterar para `"em_preparo"` ou `"pronto"`.

4. **Testes Automatizados (`backend/tests/test_concorrencia_integridade_kds.py`)**:
   - Cobertura de constraint única parcial no banco, simulação de corrida TOCTOU em `abrir_comanda`, validação cruzada de `tipo_atendimento` vs `numero_mesa`, listagem `?status=pronto` no KDS e transição `pronto -> entregue` pelo Garçom.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/models/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/comanda.py): Índice único parcial `uq_comanda_restaurante_mesa_aberta`.
- [`backend/alembic/versions/0005_indice_unico_mesa_aberta.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/versions/0005_indice_unico_mesa_aberta.py): Migração Alembic `0005`.
- [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py): Tratamento de `IntegrityError` concorrente em `abrir_comanda`.
- [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py): Validação cruzada em `ComandaCreate`.
- [`backend/src/schemas/cozinha.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/cozinha.py): Inclusão de `"pronto"` em `StatusFilaCozinha`.
- [`backend/src/controllers/v1/cozinha.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/cozinha.py): Permissão para o Garçom marcar pedido pronto como `"entregue"`.
- [`backend/tests/test_cozinha_kds.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_cozinha_kds.py) e [`backend/tests/test_comanda_pedidos.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_comanda_pedidos.py): Atualizados para o novo índice parcial e filtro `status=pronto`.
- [`backend/tests/test_concorrencia_integridade_kds.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_concorrencia_integridade_kds.py): Novos testes da Issue #38.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0017.
