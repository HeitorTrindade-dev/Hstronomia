# Agente Backend — Hstronomia

Instruções e padrões de arquitetura em camadas (**Controller ➔ Service ➔ Repository**) para a API em FastAPI.

---

## 1. Stack e Bibliotecas
- **Python**: 3.11+
- **Framework Web**: FastAPI
- **ORM**: SQLAlchemy 2.0 (Async) + `asyncpg`
- **Migrações**: Alembic
- **Validação / DTOs**: Pydantic v2
- **Configurações / Env**: `pydantic-settings`
- **Testes**: `pytest`, `pytest-asyncio`, `httpx` (para testes de API com `AsyncClient`)
- **Segurança**: Passlib (Bcrypt / Argon2) + Python-JOSE (JWT)

---

## 2. Variáveis de Ambiente e `.env.example`

- Todas as configurações da aplicação devem ser lidas exclusivamente em `src/core/config.py` utilizando `BaseSettings` do `pydantic-settings`.
- **Regra Obrigatória**: O arquivo `backend/.env.example` deve refletir todas as variáveis necessárias para subir a API localmente, incluindo:
  - `DATABASE_URL` (ex: `postgresql+asyncpg://postgres:postgres@localhost:5432/hstronomia`)
  - `SECRET_KEY` (chave para assinatura de JWTs)
  - `ALGORITHM` (ex: `HS256`)
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `CORS_ORIGINS` (ex: `http://localhost:5173`)
- **Nunca comitar `.env`**: O `.env` com senhas e segredos reais deve ser ignorado pelo [.gitignore](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/.gitignore). Ao criar qualquer nova variável, adicione-a imediatamente em `backend/.env.example`.

---

## 3. Arquitetura em Camadas (Controller ➔ Service ➔ Repository)

O fluxo de dados no backend deve **obrigatoriamente** respeitar a separação de responsabilidades:

```text
Requisição HTTP
      │
      ▼
[ Controllers / Routers ] ──▶ Validação de DTOs (Pydantic), injeção de dependências e HTTP Status
      │
      ▼
   [ Services ]            ──▶ Regras de negócio, cálculos, validações lógicas e transações
      │
      ▼
 [ Repositories ]          ──▶ Consultas ao banco via SQLAlchemy (SELECT, INSERT, UPDATE)
      │
      ▼
[ Database / Postgres ]
```

### Responsabilidades por Camada:

1. **Controllers (`src/controllers/`)**:
   - Definem as rotas HTTP (`@router.get`, `@router.post`, etc.).
   - Recebem Schemas Pydantic como entrada e retornam Schemas de saída.
   - **Proibido**: Fazer queries diretas no banco ou aplicar regras de negócio complexas aqui.

2. **Services (`src/services/`)**:
   - Orquestram o fluxo de negócio (ex: `ComandaService.adicionar_item`, `AuthService.autenticar_equipe`).
   - Calculam totais, aplicam taxas de serviço e garantem o congelamento do preço/nome do item.
   - **Proibido**: Manipular objetos de Request/Response HTTP diretamente.

3. **Repositories (`src/repositories/`)**:
   - Camada exclusiva de acesso a dados (ex: `ItemRepository`, `ComandaRepository`).
   - Recebem a sessão assíncrona do SQLAlchemy (`AsyncSession`).
   - **Regra de Ouro**: Todo método de busca/alteração **deve receber e filtrar por `restaurante_id`**.

---

## 4. Testes Automatizados (`backend/tests/`)

- Framework oficial: `pytest` com plugin `pytest-asyncio`.
- Toda regra de negócio em `src/services/` deve ter testes unitários/integração:
  - `tests/unit/`: Testes de services isolados (cálculos de subtotal, 10% taxa de serviço, descontos, congelamento de itens).
  - `tests/integration/`: Testes com banco real/in-memory validando isolamento por `restaurante_id`.
- Antes de abrir um Pull Request (`gh pr create`), execute os testes (`pytest`) para garantir que tudo passa com 100% de sucesso.

---

## 5. Estrutura de Diretórios do Backend

```text
backend/
├── .env.example                 # Exemplo documentado de variáveis necessárias
├── alembic/
│   └── versions/
├── alembic.ini
├── pyproject.toml
├── tests/                       # Testes automatizados (pytest)
│   ├── conftest.py
│   ├── unit/
│   └── integration/
└── src/
    ├── main.py
    ├── core/
    │   ├── config.py            # Variáveis de ambiente (pydantic-settings)
    │   ├── database.py          # AsyncEngine e async_sessionmaker
    │   └── security.py          # Hashing de senhas e geração/decodificação de JWT
    ├── models/                  # Entidades SQLAlchemy (Base, Mapped)
    ├── schemas/                 # DTOs Pydantic (Request / Response)
    ├── repositories/            # Camada de Acesso a Dados (SQLAlchemy)
    ├── services/                # Camada de Regras de Negócio
    └── controllers/             # Rotas / Endpoints FastAPI
```

---

## 6. Regras de Autenticação e Autorização

1. **Dono do Restaurante**:
   - Autenticação via `POST /api/v1/auth/login` (e-mail e senha).
   - Retorna JWT com `sub: dono_id` e permissão `role: "dono"`.
2. **Equipe Operacional (Garçom e Cozinha)**:
   - Endpoint: `POST /api/v1/auth/operacional`
   - Payload: `{ "slug": string, "pin": string }`
   - Se `pin == restaurante.codigo_garcom`: token com `role: "garcom"` e `restaurante_id`.
   - Se `pin == restaurante.codigo_cozinha`: token com `role: "cozinha"` e `restaurante_id`.

---

## 7. Diretrizes de Código
- Sempre utilize **Async/Await** em controllers, services e repositories.
- Use tipagem estrita com Pydantic v2 e typing moderno do Python (`int | None`, `list[ItemResponse]`).
- Repositories devem encapsular queries complexas e evitar vazamento de SQL para os Services.
