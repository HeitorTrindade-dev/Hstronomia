# 0002 — Configuração de Conexão Async (SQLAlchemy 2.0) e Alembic

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Google DeepMind)
- **Tipo de Mudança**: Database / Infraestrutura
- **Issue Vinculada**: [#2](https://github.com/HeitorTrindade-dev/Hstronomia/issues/2)
- **Status**: Concluído

---

## 1. Motivação do Registro
Configuração da camada de persistência assíncrona do backend utilizando SQLAlchemy 2.0 e driver `asyncpg`, além de estruturar o sistema de controle de versões de banco de dados com Alembic.

---

## 2. Decisões Técnicas Tomadas

1. **Instalação de Dependências**:
   - `sqlalchemy[asyncio]>=2.0.36`, `asyncpg>=0.30.0` e `alembic>=1.14.0`.

2. **Setup do Engine e Sessões Assíncronas (`backend/src/core/database.py`)**:
   - `create_async_engine` configurado com `settings.DATABASE_URL`.
   - `async_sessionmaker` com `expire_on_commit=False` e `autoflush=False`.
   - Classe `Base` herdando de `AsyncAttrs` e `DeclarativeBase`.
   - Dependency injection `get_db` em gerador assíncrono para injeção limpa de sessões nos controllers.

3. **Configuração do Alembic com Suporte Assíncrono (`backend/alembic/`)**:
   - Template assíncrono inicializado.
   - `backend/alembic/env.py` configurado para carregar `settings.DATABASE_URL` via `pydantic-settings` e `Base.metadata` como `target_metadata`.

4. **Testes Automatizados (`backend/tests/test_database.py`)**:
   - Validação da existência dos metadados da `Base`.
   - Validação de que a dependência `get_db` fornece uma `AsyncSession` ativa (100% aprovado).

---

## 3. Arquivos Criados / Modificados
- [`backend/pyproject.toml`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/pyproject.toml): Dependências adicionadas.
- [`backend/src/core/database.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/core/database.py): Engine, sessionmaker, Base e get_db.
- [`backend/alembic.ini`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic.ini): Configuração do Alembic.
- [`backend/alembic/env.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/env.py): Integração assíncrona com SQLAlchemy e Settings.
- [`backend/tests/test_database.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_database.py): Testes da camada de banco.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0002.
