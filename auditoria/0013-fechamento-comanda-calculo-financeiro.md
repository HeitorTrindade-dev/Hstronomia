# 0013 — Fechamento de Comanda e Cálculo Financeiro

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Comandas / Financeiro
- **Issue Vinculada**: [#18](https://github.com/HeitorTrindade-dev/Hstronomia/issues/18)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #18 (última issue de backend do escopo atual): permitir a conferência prévia da conta (`GET /api/v1/comandas/{id}/previa`) e o encerramento definitivo da comanda (`POST /api/v1/comandas/{id}/fechar`), calculando subtotal a partir dos preços congelados, taxa de serviço opcional de 10% e descontos em `Decimal`.

---

## 2. Decisões Técnicas Tomadas

1. **DTOs de Prévia e Fechamento (`backend/src/schemas/comanda.py`)**:
   - `MetodoPagamento`: restrito aos valores de `schema.dbml` (`"pix"`, `"dinheiro"`, `"cartao_credito"`, `"cartao_debito"`).
   - `ComandaFecharRequest`: validado com `extra="forbid"`, `incluir_taxa_servico: bool = True` e `desconto: Decimal >= 0.00`.
   - `ComandaPreviaResponse`: retorna extrato completo dos itens congelados, `subtotal`, `incluir_taxa_servico`, `taxa_servico`, `desconto` e `valor_total`.

2. **Regras de Cálculo e Encerramento (`backend/src/services/comanda.py`)**:
   - `_calcular_valores_comanda`: soma `preco_unitario * quantidade` em `Decimal` com arredondamento `ROUND_HALF_UP`, calcula 10% de taxa de serviço quando `incluir_taxa_servico=True` e bloqueia descontos negativos ou superiores ao valor bruto (`subtotal + taxa_servico`).
   - `obter_previa`: simula os valores da comanda sem alterar seu estado no banco.
   - `fechar_comanda`: exige `status == "aberta"`, grava `subtotal`, `taxa_servico`, `desconto`, `valor_total`, `metodo_pagamento`, `fechado_em = datetime.now(UTC)` e `status = "fechada"`, registrando log de auditoria (OWASP A09).

3. **Endpoints (`backend/src/controllers/v1/comanda.py`)**:
   - `GET /api/v1/comandas/{comanda_id}/previa` e `POST /api/v1/comandas/{comanda_id}/fechar` protegidos com `get_atendimento_restaurante_id` (acessíveis por Garçom e Dono; bloqueados para Cozinha com `403` e isolados contra IDOR cross-tenant).

4. **Testes Automatizados (`backend/tests/test_comanda_fechamento.py`)**:
   - Cobertura de prévia com/sem 10% e descontos, bloqueio de desconto excessivo, fechamento com liberação da mesa para novo giro, integração com `GET /api/v1/financeiro/resumo`, bloqueio de duplo fechamento, validações `extra="forbid"`, RBAC/BFLA e IDOR.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/schemas/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/comanda.py): Schemas `ComandaFecharRequest` e `ComandaPreviaResponse`.
- [`backend/src/services/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/comanda.py): Métodos `_calcular_valores_comanda`, `obter_previa` e `fechar_comanda`.
- [`backend/src/controllers/v1/comanda.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/comanda.py): Endpoints `GET /api/v1/comandas/{id}/previa` e `POST /api/v1/comandas/{id}/fechar`.
- [`backend/tests/test_comanda_fechamento.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_comanda_fechamento.py): Testes automatizados da Issue #18.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0013.
