# 0014 — Endpoints e Service de Gestão de Restaurantes (Onboarding do Dono e PINs)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Restaurantes / Autenticação
- **Issue Vinculada**: [#35](https://github.com/HeitorTrindade-dev/Hstronomia/issues/35)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #35: disponibilizar a camada de aplicação e endpoints HTTP para que o Dono recém-cadastrado possa criar seu restaurante, listar seus estabelecimentos e rotacionar os PINs operacionais (`codigo_garcom` e `codigo_cozinha`), além de permitir a consulta pública segura pelo `slug` na tela de acesso operacional (`/acesso/:slug`).

---

## 2. Decisões Técnicas Tomadas

1. **DTOs Pydantic (`backend/src/schemas/restaurante.py`)**:
   - `RestauranteCreate` e `RestaurantePinsUpdate` com `extra="forbid"` (OWASP A03), validação de `slug` URL-safe (`^[a-z0-9]+(?:-[a-z0-9]+)*$`), PINs estritamente numéricos (4 a 20 dígitos) e bloqueio de colisão (`codigo_garcom != codigo_cozinha`).
   - `RestauranteResponse`: retornado exclusivamente ao Dono proprietário.
   - `RestaurantePublicoResponse`: expõe apenas `id`, `nome` e `slug` para validação pública da tela `/acesso/:slug`, sem vazar `codigo_garcom`, `codigo_cozinha` ou `dono_id`.

2. **Regras de Negócio (`backend/src/services/restaurante.py`)**:
   - `criar_restaurante`: valida unicidade de `slug` (com fallback para `IntegrityError` concorrente retornando `409 Conflict`) e registra log sem expor PINs (OWASP A09).
   - `listar_por_dono`: retorna apenas os restaurantes pertencentes ao `dono_id` autenticado.
   - `obter_por_slug_publico`: busca normalizada por `slug` (`404` se inexistente).
   - `atualizar_pins`: valida posse (`restaurante.dono_id == dono_id`, bloqueando IDOR com `404`), impede que a atualização parcial iguale `codigo_garcom` e `codigo_cozinha` (`400`) e registra log de auditoria sanitizado.

3. **Controller (`backend/src/controllers/v1/restaurante.py`, `backend/src/main.py`)**:
   - `POST /api/v1/restaurantes` (`201 Created`, restrito ao Dono).
   - `GET /api/v1/restaurantes` (`200 OK`, restrito ao Dono).
   - `GET /api/v1/restaurantes/slug/{slug}` (`200 OK`, público com `RestaurantePublicoResponse`).
   - `PATCH /api/v1/restaurantes/{restaurante_id}/pins` (`200 OK`, restrito ao Dono).

4. **Testes Automatizados (`backend/tests/test_restaurante_api.py`)**:
   - Cobertura de criação, bloqueio de slug duplicado (`409`), listagem isolada por dono, consulta pública sem vazamento de PINs, rotação de PINs + login operacional, validações de schema (`extra="forbid"`, colisão de PINs, slug inválido), RBAC (`403` para Garçom) e IDOR (`404` cross-owner).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/schemas/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/restaurante.py): Schemas de criação, rotação de PINs e respostas privada/pública.
- [`backend/src/services/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/restaurante.py): `RestauranteService`.
- [`backend/src/controllers/v1/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/restaurante.py): Endpoints `/api/v1/restaurantes`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Registro do `restaurante_router`.
- [`backend/tests/test_restaurante_api.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_restaurante_api.py): Testes automatizados da Issue #35.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0014.
