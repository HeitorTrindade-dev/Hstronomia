# Registro de Auditoria 0028 — Screenshots e Demonstração Visual das Cenas Operacionais no README

- **Data**: 2026-11-21
- **Autor / Agente**: Antigravity (Google DeepMind)
- **Issue Atendida**: #64 — [Docs] Adicao de Screenshots das Cenas Operacionais no README
- **Branch**: feat/64-screenshots-cenas-readme

---

## 1. Motivação

Enriquecer a documentação oficial do repositório no `README.md` com evidências visuais de alta qualidade e fidelidade, demonstrando o funcionamento de ponta a ponta dos três perfis do sistema (Dono, Garçom e Cozinha KDS) com base no estabelecimento modelo fictício *Trattoria Bella Notte*.

---

## 2. Conteúdo e Decisões Técnicas

- **Criação de Script de Seed (`backend/seed_demo.py`)**:
  - Geração do perfil gestor Giovanni Rossi (`giovanni@bellanotte.com`).
  - Estabelecimento *Trattoria Bella Notte* (`slug: bella-notte`, PINs `1234` e `4321`).
  - Cardápio italiano refinado com 11 pratos, sobremesas e vinhos.
  - Comandas ativas com mesas ocupadas (Mesa 3, Mesa 7, Mesa 12 e pedido de Balcão/Viagem) em diferentes estágios de atendimento.
  - Lançamentos de despesas operacionais categorizadas para visualização dos KPIs e fluxo de caixa.
- **Automação de Capturas via Playwright (`scripts/capture_screenshots.py`)**:
  - Utilização do Playwright Chromium Headless com escala de renderização retina 2x (`device_scale_factor: 2`).
  - Geração de 6 capturas estratégicas armazenadas em `assets/screenshots/`:
    1. `01-salao-mesas.png`: Salão e mesas com semáforo ao vivo.
    2. `02-lancamento-pedido.png`: Lançamento mobile com seletor táctil e chips rápidos de cozinha.
    3. `03-fechamento-conta.png`: Fechamento com prévia financeira, switch de taxa de 10%, desconto e cálculo de troco para dinheiro.
    4. `04-cozinha-kds.png`: Cozinha KDS Kanban em Dark Mode permanente com timers de espera coloridos.
    5. `05-painel-financeiro.png`: Dashboard consolidado de receitas, despesas e saldo líquido.
    6. `06-acesso-pin.png`: Tela de autenticação por PIN com teclado virtual touch-friendly.
- **Atualização do `README.md`**:
  - Inclusão da seção *Demonstração Visual da Operação* com layout responsivo e legendas explicativas.

---

## 3. Arquivos Criados ou Modificados

- `assets/screenshots/01-salao-mesas.png` (Novo)
- `assets/screenshots/02-lancamento-pedido.png` (Novo)
- `assets/screenshots/03-fechamento-conta.png` (Novo)
- `assets/screenshots/04-cozinha-kds.png` (Novo)
- `assets/screenshots/05-painel-financeiro.png` (Novo)
- `assets/screenshots/06-acesso-pin.png` (Novo)
- `backend/seed_demo.py` (Script de seed com dados realistas)
- `scripts/capture_screenshots.py` (Script de automação Playwright)
- `README.md` (Incorporação dos screenshots)
- `auditoria/0028-screenshots-operacionais-readme.md` (Novo registro de auditoria)
- `auditoria/indice.md` (Atualizado)
