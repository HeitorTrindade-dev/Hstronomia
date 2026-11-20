# Índice de Auditoria — Hstronomia

Registro central de todas as mudanças significativas realizadas no projeto por agentes de IA ou desenvolvedores. Cada registro detalha a motivação, decisões de arquitetura e arquivos afetados.

---

## Registros de Auditoria

| Código | Data | Título | Status | Arquivo |
| :--- | :--- | :--- | :--- | :--- |
| **0005** | 2026-11-20 | Autenticação do Dono (Cadastro, Login JWT e Hash Bcrypt) | Concluído | [0005-autenticacao-dono-jwt.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0005-autenticacao-dono-jwt.md) |
| **0004** | 2026-11-20 | Models e Repositories de Dono e Restaurante | Concluído | [0004-models-e-repositories-dono-e-restaurante.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0004-models-e-repositories-dono-e-restaurante.md) |
| **0003** | 2026-11-20 | Setup Inicial do Frontend (React, Vite, TypeScript, Tailwind) | Concluído | [0003-setup-frontend-react-vite.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0003-setup-frontend-react-vite.md) |
| **0002** | 2026-11-20 | Configuração de Conexão Async (SQLAlchemy 2.0) e Alembic | Concluído | [0002-configuracao-conexao-async-e-alembic.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0002-configuracao-conexao-async-e-alembic.md) |
| **0001** | 2026-11-20 | Setup Inicial do Backend e Docker Compose | Concluído | [0001-setup-backend-e-docker-compose.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0001-setup-backend-e-docker-compose.md) |

---

## Padrão para Novos Registros

Sempre que uma mudança significativa for implementada:
1. Criar um novo arquivo em `auditoria/` nomeado sequencialmente: `XXXX-titulo-da-mudanca.md` (ex: `0006-autenticacao-operacional-pin.md`).
2. Adicionar uma nova linha no topo da tabela deste arquivo `indice.md`.
3. Detalhar:
   - Autor/Agente e Modelo de IA utilizado (ex: `Antigravity (Modelo: Gemini 3.8 Flash)`)
   - Motivação
   - Decisões Técnicas / Arquiteturais
   - Arquivos Criados ou Modificados
