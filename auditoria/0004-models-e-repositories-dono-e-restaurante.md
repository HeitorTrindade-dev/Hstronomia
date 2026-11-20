# 0004 — Models e Repositories de Dono e Restaurante

- **Data**: 2026-11-20
- **Autor/Agente**: Antigravity (Modelo: Gemini 3.8 Flash)
- **Tipo de Mudança**: Backend / Database / Models / Repositories
- **Issue Vinculada**: [#4](https://github.com/HeitorTrindade-dev/Hstronomia/issues/4)
- **Status**: Concluído

---

## 1. Motivação do Registro
Implementação da Issue #4: criação dos modelos de persistência SQLAlchemy 2.0 para `Dono` e `Restaurante`, configuração dos repositórios de acesso a dados isolados com proteção a IDOR, geração da primeira migration do Alembic e cobertura de testes automatizados com SQLite assíncrono.

---

## 2. Decisões Técnicas Tomadas

1. **Modelos SQLAlchemy 2.0 (`backend/src/models/`)**:
   - `Dono`: UUID PK, `nome`, `email` único normalizado, `senha_hash`, `criado_em` e relacionamento `cascade="all, delete-orphan"` com `Restaurante`.
   - `Restaurante`: UUID PK, `dono_id` FK (indexada), `nome`, `slug` único normalizado, `codigo_garcom`, `codigo_cozinha`, `criado_em`.

2. **Repositórios (`backend/src/repositories/`)**:
   - `BaseRepository[ModelType]`: repositório genérico com operações fundamentais (`get_by_id`, `list_all`, `delete_by_id`).
   - `DonoRepository`: herda de `BaseRepository[Dono]`, com métodos específicos `get_by_email` e `create`.
   - `RestauranteRepository`: herda de `BaseRepository[Restaurante]`, com `get_by_slug`, `get_by_dono_id`, `create` e `update_pins` (com validação estrita de posse `dono_id` contra IDOR).

3. **Migração Alembic (`backend/alembic/versions/0001_criar_tabelas_dono_e_restaurante.py`)**:
   - DDL explícito com índices em `email`, `slug` e `dono_id`.
   - `alembic heads` validado com sucesso.

4. **Testes Automatizados (`backend/tests/test_dono_restaurante.py`)**:
   - Fixture assíncrona em `conftest.py` com `sqlite+aiosqlite:///:memory:`.
   - Testes cobrindo criação, busca por e-mail/slug e bloqueio explícito de tentativa de IDOR (100% aprovados).

---

## 3. Arquivos Criados / Modificados
- [`backend/src/models/dono.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/dono.py): Modelo Dono.
- [`backend/src/models/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/restaurante.py): Modelo Restaurante.
- [`backend/src/models/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/models/__init__.py): Registro de modelos.
- [`backend/src/repositories/base.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/base.py): Repositório base genérico.
- [`backend/src/repositories/dono.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/dono.py): Repositório Dono.
- [`backend/src/repositories/restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/restaurante.py): Repositório Restaurante com trava IDOR.
- [`backend/src/repositories/__init__.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/src/repositories/__init__.py): Exportação de repositórios.
- [`backend/alembic/versions/0001_criar_tabelas_dono_e_restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/versions/0001_criar_tabelas_dono_e_restaurante.py): Migração inicial.
- [`backend/alembic/env.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/alembic/env.py): Importação de `src.models`.
- [`backend/tests/conftest.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/conftest.py): Fixture de banco de dados assíncrono para testes.
- [`backend/tests/test_dono_restaurante.py`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/backend/tests/test_dono_restaurante.py): Testes de repositório e IDOR.
- [`auditoria/indice.md`](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md): Atualizado com a entrada 0004.
