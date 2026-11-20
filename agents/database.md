# Agente Database — Hstronomia

Instruções para modelagem, migrações e persistência de dados.

---

## 1. Fonte da Verdade do Schema
O arquivo oficial com o desenho do banco é o [schema.dbml](file:///home/heitor/Documentos/workspace/projetos/pessoais/Hstronomia/schema.dbml) na raiz do repositório. Qualquer alteração de colunas ou relações deve ser refletida primeiro nele.

---

## 2. Entidades Principais
1. **`dono`**: Credenciais de login e conta do administrador.
2. **`restaurante`**: Dados do estabelecimento, slug e PINs de acesso (`codigo_garcom`, `codigo_cozinha`).
3. **`item`**: Produtos do cardápio com preço e controle de disponibilidade/ativação.
4. **`comanda`**: Mesas ou pedidos de balcão, contendo subtotal, taxa de serviço, desconto, forma de pagamento e status.
5. **`item_comanda`**: Itens adicionados à comanda, com nome e preço congelados no momento do pedido.
6. **`despesa`**: Registro de saídas financeiras do restaurante.

---

## 3. Regras de Ouro de Persistência
- **Imutabilidade**: Ao criar um registro em `item_comanda`, copie `nome` e `preco` do `item` para `nome_item` e `preco_unitario`. O histórico financeiro nunca deve sofrer alterações por reajustes posteriores no cardápio.
- **Soft Delete**: Itens do cardápio nunca sofrem `DELETE` físico se já tiverem participado de vendas; use `ativo = false`.
- **Isolamento**: Sempre inclua `restaurante_id` nas entidades operacionais.
