# 0016 — Hardening de Segurança OWASP em Autenticação, Segredos e Headers

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini)
- **Tipo de Mudança**: Backend / Segurança / Autenticação
- **Issue Vinculada**: [#37](https://github.com/HeitorTrindade-dev/Hstronomia/issues/37)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #37: corrigir vulnerabilidades OWASP identificadas na revisão completa do backend, incluindo rate limiting e mitigação de timing attack no login do Dono, normalização de e-mail e `extra="forbid"` nos schemas do Dono, revogação automática de tokens operacionais ao rotacionar PIN, validação estrita de `SECRET_KEY`/`DEBUG` em produção e headers HTTP de segurança.

---

## 2. Decisões Técnicas Tomadas

1. **Rate Limiting no Login do Dono (`backend/src/core/rate_limit.py`, `backend/src/controllers/v1/auth.py`)**:
   - Instanciado `dono_login_rate_limiter` por janela deslizante isolado por chave `ip:email_normalizado`, bloqueando tentativas de força bruta com `429 Too Many Requests` + `Retry-After` e registrando logs sem expor senhas (OWASP A07 / A09).

2. **Mitigação de Timing Attack e Normalização de E-mail (`backend/src/core/security.py`, `backend/src/services/auth.py`, `backend/src/schemas/auth.py`)**:
   - Criado `DUMMY_PASSWORD_HASH` constante; quando o e-mail informado em `autenticar_dono` não existe, `verify_password(data.senha, DUMMY_PASSWORD_HASH)` é executado para equalizar o tempo de resposta do `bcrypt` contra enumeração de e-mails.
   - `DonoCreate` e `LoginRequest` endurecidos com `extra="forbid"` (OWASP A03) e normalização de e-mail (`strip().lower()`).

3. **Revogação Automática de Tokens Operacionais ao Rotacionar PIN (`backend/src/core/security.py`, `backend/src/services/auth.py`, `backend/src/controllers/deps.py`)**:
   - `compute_pin_fingerprint(restaurante_id, role, pin)` gera um HMAC-SHA256 truncado assinado com `SECRET_KEY` e gravado na claim `pin_fp` dos tokens emitidos em `/api/v1/auth/operacional`.
   - `get_current_user` valida `pin_fp` em tempo constante (`hmac.compare_digest`) contra o PIN atual do restaurante, invalidando imediatamente (`401`) sessões antigas assim que o Dono altera `codigo_garcom` ou `codigo_cozinha`.

4. **Validação de Segredos em Produção e Headers HTTP (`backend/src/core/config.py`, `backend/src/main.py`)**:
   - `Settings.validar_seguranca_producao` bloqueia a inicialização com `ENVIRONMENT="production"` caso `SECRET_KEY` seja o valor padrão de desenvolvimento, tenha menos de 32 caracteres ou `DEBUG=True` (OWASP A02 / A05).
   - Restringidos `allow_methods` e `allow_headers` no `CORSMiddleware` e adicionado middleware HTTP injetando `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e `Referrer-Policy: no-referrer`.

5. **Testes Automatizados (`backend/tests/test_security_hardening.py`)**:
   - Cobertura de validação de `Settings` em produção, headers de segurança, `extra="forbid"`, normalização case-insensitive de e-mail, chamada a `DUMMY_PASSWORD_HASH`, bloqueio `429` no login do Dono e revogação seletiva de token operacional após rotação de PIN.

---

## 3. Arquivos Criados / Modificados
- [`backend/src/core/config.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/config.py): Validação de `SECRET_KEY` e `DEBUG` em produção.
- [`backend/src/core/security.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/security.py): `DUMMY_PASSWORD_HASH` e `compute_pin_fingerprint`.
- [`backend/src/core/rate_limit.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/rate_limit.py): `dono_login_rate_limiter`.
- [`backend/src/schemas/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/auth.py): `extra="forbid"` e normalização em `DonoCreate` e `LoginRequest`.
- [`backend/src/services/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/auth.py): Timing guard com `DUMMY_PASSWORD_HASH` e emissão da claim `pin_fp`.
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Verificação de `pin_fp` em `get_current_user`.
- [`backend/src/controllers/v1/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/auth.py): Rate limiting em `POST /api/v1/auth/login`.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Restrição de CORS e middleware de security headers.
- [`backend/tests/conftest.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/conftest.py): Reset de `dono_login_rate_limiter` entre testes.
- [`backend/tests/test_security_hardening.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_security_hardening.py): Testes automatizados da Issue #37.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0016.
