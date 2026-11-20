# Agente Frontend — Hstronomia

Instruções específicas para desenvolvimento da interface web e mobile.

---

## 1. Stack e Ferramentas
- **Framework**: React 18+ com Vite e TypeScript
- **Estilização**: Tailwind CSS (seguir estritamente o [estilos.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/estilos.md))
- **Ícones**: Lucide React
- **Roteamento**: React Router DOM v6
- **Requisições & Cache**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Guia de Design System e Cores**: Veja detalhes completos em [estilos.md](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/estilos.md)

---

## 2. Variáveis de Ambiente e `.env.example`

- No Vite, variáveis de ambiente expostas ao client **devem obrigatoriamente** começar com o prefixo `VITE_` (ex: `import.meta.env.VITE_API_URL`).
- **Regra Obrigatória**: O arquivo `frontend/.env.example` deve manter as variáveis necessárias para desenvolvimento:
  - `VITE_API_URL=http://localhost:8000/api/v1`
- **Nunca comitar `.env` ou `.env.local`**: Mantenha o [.gitignore](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/.gitignore) configurado para ignorar arquivos de ambiente locais.

---

## 3. Estrutura do Frontend (`frontend/`)

```text
frontend/
├── .env.example            # Exemplo documentado de variáveis necessárias
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── src/
    ├── assets/
    ├── components/         # Botões, modais, inputs, tabelas compartilhadas
    ├── contexts/           # AuthContext (Dono, Garçom, Cozinha)
    ├── hooks/              # Custom hooks de API e UI
    ├── pages/
    │   ├── auth/           # Login Dono (/login) e Entrada por PIN (/acesso/:slug)
    │   ├── admin/          # Painel do Dono (Cardápio, Configurações, Financeiro)
    │   ├── garcom/         # Tela de Mesas e Lançamento de Itens (Mobile-first)
    │   └── cozinha/        # KDS em tempo real (Kanban de pedidos)
    ├── services/           # Instância de Axios/Fetch e chamadas de API
    └── types/              # Tipagens TypeScript compartilhadas
```

---

## 4. Diretrizes de UX por Perfil
1. **Garçom (Mobile First)**:
   - Interface rápida, botões grandes para toque em telas móveis.
   - Poucos cliques para adicionar observação e enviar pedido para a cozinha.
2. **Cozinha (Monitor/Tablet First)**:
   - Modo visual de alto contraste e fácil leitura à distância.
   - Cards de pedidos ordenados por tempo de espera (com status: `pendente` ➔ `em_preparo` ➔ `pronto`).
3. **Painel do Dono (Desktop First)**:
   - Dashboard analítico simples: Total vendido no dia, total de despesas e lista de comandas.
   - Facilidade para alterar preços e ligar/desligar disponibilidade de itens.
