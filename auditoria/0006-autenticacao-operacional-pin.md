# 0006 — Autenticação Operacional por PIN (Garçom e Cozinha)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Segurança / Autenticação Operacional
- **Issue Vinculada**: [#6](https://github.com/HeitorTrindade-dev/Hstronomia/issues/6)
- **Status**: Concluído

---

## 1. Motivação do Registro
Conclusão da Issue #6: consolidar a autenticação operacional por `slug` + PIN numérico para Garçom e Cozinha, com expiração temporária dedicada, proteção contra força bruta (rate limiting), comparação em tempo constante e dependências específicas de autorização RBAC (`get_current_garcom` e `get_current_cozinha`).

---

## 2. Decisões Técnicas Tomadas

1. **Configurações e `.env.example` (`backend/src/core/config.py`, `backend/.env.example`)**:
   - Adicionada variável `OPERATIONAL_TOKEN_EXPIRE_MINUTES=120` para garantir expiração mais curta nas sessões operacionais em relação ao token do Dono (`ACCESS_TOKEN_EXPIRE_MINUTES=480`).
   - Adicionadas variáveis `OPERATIONAL_RATE_LIMIT_MAX_ATTEMPTS=5` e `OPERATIONAL_RATE_LIMIT_WINDOW_SECONDS=300` para controle de taxa no login por PIN.

2. **Rate Limiting por Janela Deslizante (`backend/src/core/rate_limit.py`)**:
   - Implementado `SlidingWindowRateLimiter` em memória, isolado por chave `ip:slug`.
   - Bloqueia com `429 Too Many Requests` e cabeçalho `Retry-After` ao atingir o limite de falhas consecutivas na janela configurada, e limpa o contador em caso de login bem-sucedido.
   - Logs de auditoria registram apenas IP e slug, sem expor PINs ou tokens (OWASP A09).

3. **Validação Estrita de Payload (`backend/src/schemas/auth.py`)**:
   - `OperacionalLoginRequest` endurecido com `extra="forbid"`, normalização de `slug` (`strip().lower()`) e validação de `pin` estritamente numérico (4 a 20 dígitos).

4. **Autenticação Segura no Service (`backend/src/services/auth.py`)**:
   - `AuthService.autenticar_operacional` utiliza comparação em tempo constante (`hmac.compare_digest`) contra `codigo_garcom` e `codigo_cozinha`.
   - Emite JWT com claims `sub`, `restaurante_id`, `role` (`"garcom"` ou `"cozinha"`) e TTL configurado por `OPERATIONAL_TOKEN_EXPIRE_MINUTES`.
   - Mantém mensagem genérica `401 Unauthorized` (`"Credenciais inválidas."`) tanto para slug inexistente quanto para PIN incorreto (OWASP A07).

5. **Dependências de Autorização RBAC (`backend/src/controllers/deps.py`)**:
   - `get_current_user` valida a presença e consistência da claim `restaurante_id` com `sub` para tokens operacionais.
   - Criadas as dependências `get_current_garcom` e `get_current_cozinha`, retornando `UserSession` restrita ao respectivo papel e bloqueando os demais papéis com `403 Forbidden` (OWASP API5 / BFLA).

6. **Testes Automatizados (`backend/tests/test_auth_operacional.py`, `backend/tests/conftest.py`)**:
   - Adicionado reset automático do rate limiter entre testes no `conftest.py`.
   - Criada suíte cobrindo claims/expiração temporária, normalização de slug, rejeição de PIN não numérico e campos extras, anti-enumeração, bloqueio por rate limit (`429`) e matriz completa de autorização (`get_current_garcom`, `get_current_cozinha`, `get_current_dono`, tokens malformados).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/core/config.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/config.py): Novas configurações de TTL operacional e rate limit.
- [`backend/.env.example`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/.env.example): Documentação das novas variáveis de ambiente.
- [`backend/src/core/rate_limit.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/rate_limit.py): Limitador de taxa por janela deslizante.
- [`backend/src/schemas/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/auth.py): Endurecimento de `OperacionalLoginRequest`.
- [`backend/src/services/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/auth.py): Comparação timing-safe e expiração temporária dedicada.
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Validação de `restaurante_id` e dependências `get_current_garcom` e `get_current_cozinha`.
- [`backend/src/controllers/v1/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/auth.py): Integração de rate limiting e logs sanitizados no endpoint `POST /api/v1/auth/operacional`.
- [`backend/tests/conftest.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/conftest.py): Fixture de limpeza do rate limiter entre testes.
- [`backend/tests/test_auth_operacional.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_auth_operacional.py): Testes unitários e de integração da Issue #6.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0006.
