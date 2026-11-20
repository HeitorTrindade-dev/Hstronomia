---
name: Feature / Tarefa
about: Padrão oficial de especificação de funcionalidades e tarefas do Hstronomia
title: '[Módulo] Descrição concisa'
labels: ['feature']
assignees: ''
---

### Contexto e Objetivo
Breve descrição do problema a ser resolvido e o objetivo da entrega para o sistema.

---

### Checklist de Implementação
- [ ] Tarefa técnica 1
- [ ] Tarefa técnica 2
- [ ] Tarefa técnica 3

---

### Critérios de Aceite
- [ ] Regra de negócio funcionando conforme esperado.
- [ ] Isolamento de restaurante_id garantido nas consultas.
- [ ] Desenvolvido na branch feat/<nome-da-feature>.
- [ ] Mensagens de commit seguindo o padrão Conventional Commits (feat: ...).
- [ ] Registro de auditoria criado em auditoria/XXXX-titulo.md e atualizado em auditoria/indice.md.

---

### Camadas e Arquivos
- Controller: backend/src/controllers/...
- Service: backend/src/services/...
- Repository: backend/src/repositories/...
- Frontend: frontend/src/...
