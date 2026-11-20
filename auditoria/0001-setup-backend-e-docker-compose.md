# 0001 — Setup Inicial do Backend e Docker Compose

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Google DeepMind)
- **Tipo de Mudança**: Setup / Infraestrutura
- **Issue Vinculada**: [#1](https://github.com/HeitorTrindade-dev/Hstronomia/issues/1)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #1 do projeto: configuração da fundação do backend em FastAPI (Python 3.12+), definição do gerenciamento de dependências com `pyproject.toml`, orquestração do banco de dados PostgreSQL com Docker Compose, configuração de variáveis de ambiente com `pydantic-settings` e teste automatizado de health check.

---

## 2. Decisões Técnicas Tomadas

1. **Definição de Dependências (`backend/pyproject.toml`)**:
   - `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`.
   - Dependências de desenvolvimento e testes: `pytest`, `pytest-asyncio`, `httpx`, `ruff`.

2. **Infraestrutura com Docker Compose (`docker-compose.yml`)**:
   - Serviço `postgres:15-alpine` configurado com volume nomeado persistente `postgres_data`.
   - Health check com `pg_isready` a cada 5 segundos.
   - Variáveis configuráveis com fallback para ambiente de desenvolvimento local.

3. **Gerenciamento de Configuração (`backend/src/core/config.py` e `.env.example`)**:
   - Centralização de configurações utilizando `pydantic-settings` (`BaseSettings`).
   - `.env.example` documentando todas as variáveis obrigatórias.

4. **Aplicação FastAPI e Roteamento Base (`backend/src/main.py`)**:
   - Configuração de middleware CORS permitindo origens locais do frontend Vite.
   - Endpoint de verificação de integridade `GET /api/v1/health`.

5. **Testes Automatizados (`backend/tests/test_health.py`)**:
   - Teste assíncrono com `httpx.AsyncClient` e `ASGITransport` cobrindo o endpoint `/api/v1/health` (100% aprovado via `pytest`).

---

## 3. Arquivos Criados / Modificados
- [`docker-compose.yml`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/docker-compose.yml): Orquestração do PostgreSQL.
- [`backend/pyproject.toml`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/pyproject.toml): Configuração de pacotes e pytest.
- [`backend/README.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/README.md): Guia de execução local.
- [`backend/.env.example`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/.env.example): Template de variáveis de ambiente.
- [`backend/src/core/config.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/config.py): Configurações validadas com Pydantic.
- [`backend/src/main.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/main.py): Instância do FastAPI e endpoint de healthcheck.
- [`backend/tests/test_health.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_health.py): Teste do health check.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0001.
