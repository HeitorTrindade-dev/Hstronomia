# Diretrizes de Segurança para Agentes — Hstronomia

Guia exaustivo de segurança defensiva cobrindo o **OWASP Web Top 10** e o **OWASP API Security Top 10**, com diretrizes práticas para o ecossistema FastAPI (Python) e React (Vite).

---

## 1. OWASP Web & API: Matriz Completa de Prevenção

### A01 / API1 & API5: Broken Access Control & BOLA/BFLA (Controle de Acesso Quebrado)
- **IDOR / BOLA (Insecure Direct Object Reference)**:
  - Nunca busque registros usando apenas a chave primária vinda do cliente (ex: `/api/v1/comandas/{id}`).
  - Toda operação de leitura, escrita ou deleção deve filtrar por `restaurante_id`:
    ```python
    # Correto:
    stmt = select(Comanda).where(Comanda.id == comanda_id, Comanda.restaurante_id == current_user.restaurante_id)
    ```
- **BFLA (Broken Function Level Authorization)**:
  - Garçom e Cozinha **nunca** podem acessar rotas do Dono (financeiro, relatórios, alteração de cardápio).
  - Rotas devem validar explicitamente o papel (`role`) do usuário através de dependências do FastAPI (`get_current_dono`, `get_current_garcom`, etc.).

---

### A02 / API2: Cryptographic Failures & Broken Authentication (Falhas Criptográficas e Autenticação)
- **Armazenamento de Senhas**:
  - Proibido armazenar senhas em texto puro. Utilizar **Argon2id** ou **Bcrypt** com salt automático gerado por biblioteca segura (`passlib`).
- **Segurança de Tokens JWT**:
  - Assinatura com algoritmo `HS256` utilizando chave simétrica de no mínimo 256 bits (32 caracteres pseudoaleatórios criptográficos).
  - Obrigatoriedade de claim `exp` (tempo de expiração curto para sessões operacionais).
- **Tratamento de Segredos**:
  - `SECRET_KEY`, credenciais de banco e senhas jamais devem existir no código-fonte. Uso restrito a variáveis de ambiente via `pydantic-settings`.

---

### A03 / API3: Injection & Mass Assignment (Injeção e Atribuição em Massa)
- **SQL Injection**:
  - Proibido uso de queries cruas com interpolação de strings (`text(f"SELECT ... WHERE id = '{id}'")`).
  - Uso obrigatório de ORM e consultas tipadas com SQLAlchemy 2.0 (`select()`, `insert()`, `update()`).
- **Command & Template Injection**:
  - Proibido uso de funções que executam código dinâmico (`eval()`, `exec()`, `os.system()` com dados de usuário).
- **Mass Assignment / Excess Data Exposure**:
  - Nunca passe payloads brutos do cliente direto para o model do SQLAlchemy (ex: `Model(**request.dict())`).
  - Use Schemas Pydantic específicos para criação (`ItemCreate`) e atualização (`ItemUpdate`), rejeitando campos não permitidos (`extra="forbid"` em DTOs sensíveis).

---

### A04 / API6: Insecure Design & Business Flows (Design Inseguro e Fraudes de Negócio)
- **Imutabilidade de Vendas**:
  - Todo item adicionado a uma comanda congela estaticamente `nome_item` e `preco_unitario` no momento da compra. Alterações posteriores no cardápio não podem alterar históricos contábeis.
- **Precisão Financeira**:
  - Proibido o uso de `float` para lidar com moeda. Usar `Decimal` no Python e `decimal(10,2)` no PostgreSQL para evitar erros de arredondamento IEEE 754.
- **Transações Atômicas**:
  - Fechamento de mesa e baixa de pedidos devem ser executados dentro de transações de banco (`async with session.begin():`).

---

### A05 / API8: Security Misconfiguration (Configuração Insegura)
- **CORS Restritivo**:
  - Nunca use `allow_origins=["*"]` associado a `allow_credentials=True`. As origens devem ser explicitamente carregadas do `.env` (`CORS_ORIGINS`).
- **Exposição de Stack Traces**:
  - Em produção (`DEBUG=False`), a API jamais deve vazar rastreamento de pilha (stack trace) em respostas de erro. Tratar exceções com handlers padronizados e `HTTPException`.
- **Segurança no Git**:
  - O arquivo `.gitignore` deve proibir qualquer variação de arquivo `.env` (exceto `.env.example`).

---

### A06: Vulnerable and Outdated Components (Dependências Vulneráveis)
- **Checagem de Dependências**:
  - Auditoria regular via `npm audit` (frontend) e `pip-audit` / verificação de CVEs no `pyproject.toml`.
  - Fixar versões com ranges seguros (`fastapi>=0.115.0,<1.0.0`).

---

### A07 / API4: Identification Failures & Unrestricted Resource Consumption (Força Bruta e DoS)
- **Enumeração de Usuários**:
  - Respostas a falhas de autenticação devem ser genéricas: `"Credenciais inválidas"` (nunca `"Usuário não encontrado"` ou `"Senha incorreta"`).
- **Força Bruta em PINs (Rate Limiting)**:
  - PINs operacionais de Garçom/Cozinha possuem 6 dígitos. O endpoint `/api/v1/auth/operacional` deve implementar controle de taxa (limite de tentativas por IP/slug).
- **Paginação e Limite de Consultas**:
  - Endpoints de listagem (`GET /api/v1/comandas`, `GET /api/v1/itens`) devem ter limite máximo de paginação para evitar sobrecarga de memória (ex: `limit: int = Query(default=50, le=100)`).

---

### A08 / API10: Software and Data Integrity Failures (Integridade de Dados)
- **Desserialização Segura**:
  - Não utilizar `pickle` para dados vindos de fontes externas ou cookies.
- **Integridade da Build**:
  - Bloqueio de scripts arbitrários no frontend. Usar bibliotecas consolidadas e tipadas no TypeScript.

---

### A09: Security Logging and Monitoring Failures (Falhas de Monitoramento e Logs)
- **Sanitização de Logs (Data Leakage)**:
  - Nunca registrar nos logs: senhas, hashes, PINs, tokens de autenticação ou cabeçalhos sensíveis (`Authorization`).
- **Auditoria de Eventos Críticos**:
  - Registrar eventos de segurança: tentativas falhas consecutivas de login, fechamentos de comanda, estornos e alterações de preço de cardápio.

---

### A10 / API7: Server-Side Request Forgery (SSRF) & Cross-Site Scripting (XSS)
- **SSRF**:
  - O backend não deve efetuar requisições HTTP a URLs fornecidas arbitrariamente por usuários.
- **XSS (Frontend)**:
  - No React, não utilizar `dangerouslySetInnerHTML`.
  - Confiar no escape automático padrão do JSX contra injeção de scripts no DOM.

---

## 2. Checklist Rápido de Segurança para Novos Endpoints

Antes de submeter qualquer PR com novos endpoints, valide:

- [ ] A rota valida `restaurante_id` pertencente ao usuário logado?
- [ ] A rota está protegida com a role correta (`dono`, `garcom`, `cozinha`)?
- [ ] O payload de entrada é validado por um schema Pydantic?
- [ ] Não há concatenação manual de strings em comandos SQL?
- [ ] Valores monetários estão tipados como `Decimal`?
- [ ] Nenhuma informação sensível (senhas/PINs/tokens) está sendo exposta no log ou na resposta JSON?
