# Hstronomia Backend API

Backend em FastAPI para o sistema de gestão de restaurantes Hstronomia.

## Requisitos
- Python 3.11+
- Docker & Docker Compose

## Instalação e Execução

1. Crie o ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Instale as dependências:
   ```bash
   pip install -e ".[dev]"
   ```

3. Suba o banco de dados PostgreSQL com Docker Compose:
   ```bash
   docker compose up -d
   ```

4. Execute o servidor de desenvolvimento:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

5. Acesse a documentação interativa Swagger:
   - http://localhost:8000/docs
