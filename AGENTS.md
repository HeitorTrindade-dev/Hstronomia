# AGENTS.md — Hstronomia

Central de diretrizes e regras para agentes de IA atuando no repositório **Hstronomia**.

As instruções detalhadas por área de atuação estão organizadas na pasta [agents/](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents):

- 📖 **Visão Geral e Convenções Gerais**: [agents/README.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/README.md)
- ⚙️ **Backend (FastAPI, SQLAlchemy, Auth)**: [agents/backend.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/backend.md)
- 💻 **Frontend (React, Vite, Tailwind)**: [agents/frontend.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/frontend.md)
- 🔒 **Segurança & OWASP**: [agents/security.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/security.md)
- 🗄️ **Banco de Dados & Schema**: [agents/database.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/database.md) e [schema.dbml](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/schema.dbml)
- 📋 **Trilha de Auditoria**: [auditoria/indice.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md)

---

## Regras Globais Inegociáveis

1. **Multi-tenant / Isolamento de Restaurante**:
   - Todas as consultas, alterações e exclusões de entidades operacionais (`item`, `comanda`, `item_comanda`, `despesa`) **devem obrigatoriamente** filtrar por `restaurante_id`.
2. **Imutabilidade Histórica de Vendas**:
   - Toda adição a `item_comanda` congela `nome_item` e `preco_unitario` do item original.
   - Itens do cardápio não sofrem `DELETE` físico (`ativo = False` para soft delete).
3. **Autenticação Operacional por PIN**:
   - Garçom e Cozinha acessam via `slug` + PIN numérico, gerando sessão temporária com permissão restrita à sua respectiva função.
4. **Registro Obrigatório de Auditoria**:
   - A cada grande mudança (criação de módulo, refatoração de arquitetura, alteração de schema, etc.), o agente **deve obrigatoriamente**:
     1. Criar um novo arquivo em `auditoria/XXXX-titulo.md` explicando a mudança, motivação e arquivos afetados.
     2. Registrar a entrada no arquivo [auditoria/indice.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/indice.md).
5. **Segurança de Variáveis de Ambiente e `.gitignore`**:
   - **Arquivos `.env` reais JAMAIS devem ser versionados ou commitados**. O [.gitignore](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/.gitignore) deve sempre conter `.env` e variações (`.env.*`), com exceção de `.env.example`.
   - **Manutenção obrigatória do `.env.example`**: Sempre que uma nova variável for introduzida no backend ou frontend, o respectivo `.env.example` deve ser atualizado imediatamente.
6. **Fluxo de Issue-Driven Development e Pull Requests**:
   - Para qualquer solicitação, funcionalidade ou correção:
     - **Verificação de Issue**: Verificar se já existe uma issue aberta no GitHub (`gh issue list`).
     - **Verificação e Gestão de Labels**:
       - Antes de criar a issue, o agente **deve verificar as labels existentes** (`gh label list`).
       - Identificar as labels que se encaixam (Stack, Módulo de Negócio, Tipo).
       - Se houver necessidade de uma categoria nova não contemplada pelas labels existentes, o agente **deve criar a nova label** (`gh label create`) antes de abrir a issue.
       - A issue **deve ser criada obrigatoriamente vinculada às labels correspondentes** (`gh issue create --label "..."`).
     - **Criação da Issue**: Se não existir, criar no GitHub com o template oficial ([.github/ISSUE_TEMPLATE/feature.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/.github/ISSUE_TEMPLATE/feature.md)) sem emojis.
     - **Padrão de Branches (`feat/<numero>-...`)**: Todo e qualquer desenvolvimento **deve ser feito em uma branch no padrão `feat/<numero>-<nome-da-feature>`** (ex: `feat/2-conexao-async-alembic`, `feat/5-auth-jwt-dono`, ou `fix/<numero>-...` para correções). **Nunca desenvolver diretamente na `main`**.
     - **Padrão de Commits (`feat: ...`)**: Todas as mensagens de commit **devem seguir estritamente o padrão Conventional Commits** (ex: `feat: configurar backend e docker compose`, `fix: corrigir calculo da taxa de servico`).
     - **Commits Atômicos em Issues Grandes**: Se a issue for extensa ou abranger múltiplas camadas (ex: model + service + controller), **deve-se quebrar o trabalho em commits atômicos e incrementais** ao longo do desenvolvimento, evitando commits gigantescos com tudo misturado.
     - **Abertura de Pull Request (PR)**: Ao concluir a implementação e os testes da issue, o agente **deve obrigatoriamente abrir um Pull Request** via GitHub CLI:
       ```bash
       gh pr create --title "feat: <descricao da entrega>" --body "Closes #<numero-da-issue>" --base main
       ```
       O merge na `main` ocorre após validação do PR.
7. **Testes Automatizados para Regras Críticas**:
   - Todo Service com regras críticas de negócio (cálculos financeiros, taxas de serviço, descontos, autenticação de PIN e congelamento de itens) **deve obrigatoriamente** possuir testes automatizados via `pytest` no backend antes da abertura do PR.
8. **Segurança Ofensiva e Defensiva (OWASP)**:
   - Todo agente deve seguir estritamente o guia [agents/security.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/agents/security.md).
   - Bloqueio estrito de IDOR (sempre validar `restaurante_id` junto ao `id` da entidade).
   - Proibição de SQL Injection (somente queries parametrizadas com ORM).
   - Tipos monetários exclusivamente em `Decimal`.
   - Mensagens de autenticação genéricas contra enumeração de usuários.
