# 0005 — Autenticação do Dono (Cadastro, Login JWT e Hash Bcrypt)

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini 3.8 Flash)
- **Tipo de Mudança**: Backend / Segurança / Autenticação
- **Issue Vinculada**: [#5](https://github.com/HeitorTrindade-dev/Hstronomia/issues/5)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #5: camada de autenticação segura para proprietários de restaurantes, incluindo hashing criptográfico de senhas, emissão e validação de tokens JWT, controle de acesso e endpoints protegidos.

---

## 2. Decisões Técnicas Tomadas

1. **Criptografia e Segurança (`backend/src/core/security.py`)**:
   - `hash_password` e `verify_password` implementados com `bcrypt` (12 rounds de salt automático).
   - `create_access_token` e `decode_access_token` utilizando `pyjwt` com algoritmo `HS256`, expiração automática e assinatura com `settings.SECRET_KEY`.

2. **DTOs Pydantic (`backend/src/schemas/auth.py`)**:
   - `DonoCreate` com validação de formato de e-mail (`EmailStr`) e restrição de senha mínima.
   - `DonoResponse` omitindo o hash da senha.
   - `LoginRequest` e `TokenResponse`.

3. **Camada de Negócio (`backend/src/services/auth.py`)**:
   - `cadastrar_dono`: valida duplicidade de e-mail e salva senha hasheada via `DonoRepository`.
   - `autenticar_dono`: valida credenciais com erro genérico padronizado (`401 Unauthorized - "Credenciais inválidas"`), mitigando enumeração de usuários (OWASP A07).
   - `obter_dono_por_id`: busca de perfil por UUID.

4. **Injeção de Dependência e RBAC (`backend/src/controllers/deps.py`)**:
   - `get_current_dono`: intercepta Bearer token via `HTTPBearer`, valida assinatura/expiração, restringe `role == "dono"` e injeta o objeto `Dono` autenticado.

5. **Controllers (`backend/src/controllers/v1/auth.py`)**:
   - `POST /api/v1/auth/cadastrar` (status 201).
   - `POST /api/v1/auth/login` (status 200, retorna JWT).
   - `GET /api/v1/auth/me` (status 200, rota protegida).

6. **Testes Automatizados (`backend/tests/test_auth.py`)**:
   - 8/8 testes cobrindo hash, JWT, cadastro com sucesso, bloqueio de e-mail duplicado, login com falha/sucesso e rota protegida (100% aprovados).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/core/security.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/security.py): Hashing e JWT.
- [`backend/src/schemas/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/schemas/auth.py): Schemas Pydantic.
- [`backend/src/services/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/services/auth.py): Regras de negócio de auth.
- [`backend/src/controllers/deps.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/deps.py): Dependência get_current_dono.
- [`backend/src/controllers/v1/auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/controllers/v1/auth.py): Rotas de autenticação.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Inclusão do router de autenticação.
- [`backend/tests/test_auth.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_auth.py): Testes automatizados.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0005.
