# Diretrizes para Agentes de IA — Hstronomia

Esta pasta centraliza todas as instruções, regras de negócio e convenções para agentes que atuam no desenvolvimento do **Hstronomia**.

---

## Estrutura da Pasta `agents/`

1. **[backend.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/backend.md)**:
   - Diretrizes de desenvolvimento da API em FastAPI.
   - Padrão arquitetural Controller ➔ Service ➔ Repository.
   - Padrões de SQLAlchemy 2.0 (Async) e Alembic.
   - Testes automatizados com `pytest` e `pytest-asyncio`.
   - Autenticação (Dono via JWT, Garçom/Cozinha via PIN).
   - Segurança e isolamento multi-tenant (`restaurante_id`).

2. **[frontend.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/frontend.md)**:
   - Padrões de interface em React 18+ com Vite e TypeScript.
   - Estilização com Tailwind CSS e ícones Lucide.
   - Estrutura das 3 telas: Painel do Dono, App do Garçom e KDS da Cozinha.
   - Comunicação com a API e gerenciamento de estado.

3. **[database.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/database.md)**:
   - Modelo de dados oficial (referenciando `../schema.dbml`).
   - Regras de imutabilidade de pedidos e histórico.
   - Regras de soft delete.

---

## Regras de Ouro Globais

- **Issue-Driven Development & Labels**:
  - Nenhuma linha de código deve ser escrita sem uma issue correspondente no GitHub.
  - Antes de criar a issue, verifique as labels existentes (`gh label list`). Se necessário, crie a nova label (`gh label create`) e aplique todas as labels cabíveis na abertura da issue.
- **Padrão de Branches, Commits e Pull Requests**:
  - Branches: sempre no padrão `feat/<numero>-<nome-da-feature>` (ou `fix/<numero>-<nome>` para correções). Ex: `feat/2-conexao-async-alembic`.
  - Commits: sempre no padrão Conventional Commits (`feat: <mensagem>`, `fix: <mensagem>`).
  - Pull Requests: ao concluir e testar a issue, abra o PR via `gh pr create --title "..." --body "Closes #..."`.
- **Testes Obrigatórios**: Regras de negócio em Services devem ser cobertas por testes automatizados antes do PR.
- **Isolamento de Restaurante**: Nenhuma query, leitura ou gravação de dados operacionais (itens, comandas, despesas) pode ser feita sem filtrar explicitamente pelo `restaurante_id`.
- **Histórico Intocável**: Preços e nomes de itens devem ser congelados no momento do pedido na tabela `item_comanda`.
- **Auditoria Obrigatória**: Toda mudança relevante deve gerar um registro em `auditoria/XXXX-titulo.md` e ser listada no [auditoria/indice.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md).
- **Segurança de Segredos**: Nunca versionar arquivos `.env`, mantendo `.env.example` e `.gitignore` sempre íntegros.
