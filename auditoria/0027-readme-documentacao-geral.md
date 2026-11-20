# Registro de Auditoria 0027 — Documentação Oficial do Repositório (README.md)

- **Data**: 2026-11-20
- **Autor / Agente**: Antigravity (Google DeepMind)
- **Issue Atendida**: #62 — [Docs] README Completo, Arquitetura, Guia de Execucao e Design do Sistema
- **Branch**: feat/62-readme-documentacao

---

## 1. Motivação

Estruturar a documentação principal do projeto Hstronomia no arquivo `README.md`, fornecendo aos desenvolvedores, operadores e interessados uma visão abrangente do sistema, seus três perfis de uso (Dono, Garçom, Cozinha KDS), a arquitetura técnica, salvaguardas de segurança OWASP e instruções claras de execução com Docker Compose em um único comando.

---

## 2. Conteúdo e Decisões Técnicas

- **Visão Geral e Proposta de Valor**: Descrição objetiva dos papéis do Dono, Garçom e Cozinha KDS.
- **Diferenciais de Negócio**: Documentação do isolamento multi-tenant obrigatório, autenticação operacional por PIN, imutabilidade histórica de vendas via congelamento de itens e precisão financeira com `Decimal`.
- **Diagrama Mermaid**: Visualização da arquitetura em camadas (Clientes SPA -> Nginx -> FastAPI -> SQLAlchemy 2.0 -> PostgreSQL).
- **Guia de Instalação Rápida**: Passo a passo com `docker compose up -d --build` e mapeamento das portas de acesso (`5173`, `8000`, `5433`).
- **Segurança OWASP**: Detalhamento das defesas contra IDOR, SQL Injection, Brute-Force (Rate Limit 429) e sanitização de dados com Pydantic v2.
- **Trilha de Auditoria**: Referência explícita ao diretório `auditoria/` e ao arquivo `indice.md`.

---

## 3. Arquivos Criados ou Modificados

- `README.md` (Criada documentação completa com arquitetura, diagramas e guia de execução)
- `auditoria/0027-readme-documentacao-geral.md` (Registro da auditoria 0027)
- `auditoria/indice.md` (Atualização da tabela de auditoria)
