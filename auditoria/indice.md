# Índice de Auditoria — Hstronomia

Registro central de todas as mudanças significativas realizadas no projeto por agentes de IA ou desenvolvedores. Cada registro detalha a motivação, decisões de arquitetura e arquivos afetados.

---

## Registros de Auditoria

| Código | Data | Título | Status | Arquivo |
| :--- | :--- | :--- | :--- | :--- |
| **0001** | 2026-11-20 | Setup Inicial do Backend e Docker Compose | Concluído | [0001-setup-backend-e-docker-compose.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/auditoria/0001-setup-backend-e-docker-compose.md) |

---

## Padrão para Novos Registros

Sempre que uma mudança significativa for implementada:
1. Criar um novo arquivo em `auditoria/` nomeado sequencialmente: `XXXX-titulo-da-mudanca.md` (ex: `0002-configuracao-conexao-async-e-alembic.md`).
2. Adicionar uma nova linha no topo da tabela deste arquivo `indice.md`.
3. Detalhar:
   - Motivação
   - Decisões Técnicas / Arquiteturais
   - Arquivos Criados ou Modificados
