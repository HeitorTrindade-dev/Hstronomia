# 0015 — Listagem, Detalhamento e Cancelamento de Comandas

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Comandas
- **Issue Vinculada**: [#36](https://github.com/HeitorTrindade-dev/Hstronomia/issues/36)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #36: expor os endpoints de listagem filtrada (`GET /api/v1/comandas`), detalhamento de comanda com seus itens congelados (`GET /api/v1/comandas/{id}`) e cancelamento de comanda aberta (`POST /api/v1/comandas/{id}/cancelar`), completando o ciclo de estados previsto no `schema.dbml` (`aberta`, `fechada`, `cancelada`) e viabilizando as telas de Mapa de Mesas e Balcão do Garçom.

---

## 2. Decisões Técnicas Tomadas

1. **DTOs (`backend/src/schemas/comanda.py`)**:
   - Adicionados `StatusComanda = Literal["aberta", "fechada", "cancelada"]`, `TipoAtendimento = Literal["mesa", "balcao", "viagem"]` e `ComandaDetalheResponse(ComandaResponse)` contendo `itens: list[ItemComandaResponse]`.

2. **Repositório e Service (`backend/src/repositories/comanda.py`, `backend/src/services/comanda.py`)**:
   - `ComandaRepository.cancelar`: atualiza `status = "cancelada"` e `fechado_em = datetime.now(UTC)` com isolamento estrito por `restaurante_id`.
   - `ComandaService.listar_comandas`: lista comandas filtradas por `status` e `tipo_atendimento` com paginação (`limit <= 100`, `offset`).
   - `ComandaService.obter_comanda`: retorna os dados da comanda e todos os seus itens congelados (`404` se não existir no restaurante).
   - `ComandaService.cancelar_comanda`: exige `status == "aberta"` (`400` caso já fechada ou cancelada), libera a mesa para novo atendimento, remove os itens da fila ativa do KDS e não contabiliza o valor em `somar_vendas_fechadas_periodo`.

3. **Endpoints (`backend/src/controllers/v1/comanda.py`)**:
   - `GET /api/v1/comandas`
   - `GET /api/v1/comandas/{comanda_id}`
   - `POST /api/v1/comandas/{comanda_id}/cancelar`
   - Todas as rotas protegidas por `get_atendimento_restaurante_id` (acessíveis por Garçom e Dono, bloqueadas para Cozinha com `403`).

4. **Testes Automatizados (`backend/tests/test_comanda_listagem_cancelamento.py`)**:
   - Cobertura de listagem e filtros (`status`, `tipo_atendimento`), detalhamento com itens congelados, cancelamento com liberação de mesa, verificação de exclusão da fila KDS e do faturamento financeiro, RBAC e IDOR.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/repositories/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/comanda.py): Método `cancelar`.
- [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py): Tipos `StatusComanda`, `TipoAtendimento` e schema `ComandaDetalheResponse`.
- [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py): Métodos `listar_comandas`, `obter_comanda` e `cancelar_comanda`.
- [`backend/src/controllers/v1/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/comanda.py): Endpoints `GET /comandas`, `GET /comandas/{id}` e `POST /comandas/{id}/cancelar`.
- [`backend/tests/test_comanda_listagem_cancelamento.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_comanda_listagem_cancelamento.py): Testes automatizados da Issue #36.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0015.
