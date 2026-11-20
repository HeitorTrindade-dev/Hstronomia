from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.repositories.comanda import ComandaRepository
from src.repositories.dono import DonoRepository
from src.repositories.item import ItemRepository
from src.repositories.item_comanda import ItemComandaRepository
from src.repositories.restaurante import RestauranteRepository


async def _criar_cenario_dois_restaurantes_com_itens(db_session: AsyncSession):
    dono_repo = DonoRepository(db_session)
    rest_repo = RestauranteRepository(db_session)
    item_repo = ItemRepository(db_session)

    dono_a = await dono_repo.create(
        nome="Dono A",
        email="comanda_a@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_a = await rest_repo.create(
        dono_id=dono_a.id,
        nome="Restaurante A",
        slug="comanda-rest-a",
        codigo_garcom="111111",
        codigo_cozinha="222222",
    )
    item_a = await item_repo.create(
        restaurante_id=rest_a.id,
        nome="Filé Parmegiana",
        descricao="Acompanha arroz e fritas",
        preco=Decimal("64.90"),
    )

    dono_b = await dono_repo.create(
        nome="Dono B",
        email="comanda_b@hstronomia.com",
        senha_hash=hash_password("senha_123456"),
    )
    rest_b = await rest_repo.create(
        dono_id=dono_b.id,
        nome="Restaurante B",
        slug="comanda-rest-b",
        codigo_garcom="333333",
        codigo_cozinha="444444",
    )
    item_b = await item_repo.create(
        restaurante_id=rest_b.id,
        nome="Lasanha Bolonhesa",
        descricao=None,
        preco=Decimal("49.00"),
    )
    await db_session.commit()
    return rest_a, item_a, rest_b, item_b


@pytest.mark.asyncio
async def test_comanda_repository_abertas_mesa_balcao_fechamento_e_idor(db_session: AsyncSession):
    rest_a, _, rest_b, _ = await _criar_cenario_dois_restaurantes_com_itens(db_session)
    repo = ComandaRepository(db_session)

    # Cria comandas no restaurante A (mesa e balcão) e restaurante B (mesma mesa 4)
    comanda_mesa_a = await repo.create(
        restaurante_id=rest_a.id,
        numero_mesa=4,
        identificador="Mesa 04",
        tipo_atendimento="mesa",
    )
    comanda_balcao_a = await repo.create(
        restaurante_id=rest_a.id,
        numero_mesa=None,
        identificador="Balcão - João",
        tipo_atendimento="balcao",
    )
    comanda_mesa_b = await repo.create(
        restaurante_id=rest_b.id,
        numero_mesa=4,
        identificador="Mesa 04",
        tipo_atendimento="mesa",
    )
    await db_session.commit()

    # Busca aberta por mesa respeita isolamento por restaurante_id
    encontrada_a = await repo.get_aberta_por_mesa(rest_a.id, 4)
    encontrada_b = await repo.get_aberta_por_mesa(rest_b.id, 4)
    assert encontrada_a is not None and encontrada_a.id == comanda_mesa_a.id
    assert encontrada_b is not None and encontrada_b.id == comanda_mesa_b.id

    # Proteção IDOR em get_by_id_and_restaurante
    assert await repo.get_by_id_and_restaurante(comanda_mesa_a.id, rest_b.id) is None

    # Listagem de abertas com filtro por tipo_atendimento
    abertas_a = await repo.list_abertas(rest_a.id)
    assert {c.id for c in abertas_a} == {comanda_mesa_a.id, comanda_balcao_a.id}

    abertas_balcao_a = await repo.list_abertas(rest_a.id, tipo_atendimento="balcao")
    assert [c.id for c in abertas_balcao_a] == [comanda_balcao_a.id]

    # Tentativa de update_totais e fechar cross-tenant -> None
    assert (
        await repo.update_totais(
            comanda_id=comanda_mesa_a.id,
            restaurante_id=rest_b.id,
            subtotal=Decimal("100.00"),
        )
        is None
    )
    agora = datetime.now(UTC)
    assert (
        await repo.fechar(
            comanda_id=comanda_mesa_a.id,
            restaurante_id=rest_b.id,
            subtotal=Decimal("100.00"),
            taxa_servico=Decimal("10.00"),
            desconto=Decimal("0.00"),
            valor_total=Decimal("110.00"),
            metodo_pagamento="pix",
            fechado_em=agora,
        )
        is None
    )

    # Fechamento legítimo no restaurante A
    fechada = await repo.fechar(
        comanda_id=comanda_mesa_a.id,
        restaurante_id=rest_a.id,
        subtotal=Decimal("100.00"),
        taxa_servico=Decimal("10.00"),
        desconto=Decimal("5.00"),
        valor_total=Decimal("105.00"),
        metodo_pagamento="pix",
        fechado_em=agora,
    )
    await db_session.commit()

    assert fechada is not None
    assert fechada.status == "fechada"
    assert fechada.valor_total == Decimal("105.00")
    assert fechada.metodo_pagamento == "pix"
    assert await repo.get_aberta_por_mesa(rest_a.id, 4) is None

    # Consolidação financeira de vendas fechadas no período isolada por restaurante
    total_a = await repo.somar_vendas_fechadas_periodo(
        rest_a.id,
        inicio=agora - timedelta(minutes=5),
        fim=agora + timedelta(minutes=5),
    )
    total_b = await repo.somar_vendas_fechadas_periodo(rest_b.id)
    assert total_a == Decimal("105.00")
    assert total_b == Decimal("0.00")


@pytest.mark.asyncio
async def test_item_comanda_repository_congelamento_status_kds_e_idor(db_session: AsyncSession):
    rest_a, item_a, rest_b, item_b = await _criar_cenario_dois_restaurantes_com_itens(db_session)
    comanda_repo = ComandaRepository(db_session)
    item_comanda_repo = ItemComandaRepository(db_session)
    item_repo = ItemRepository(db_session)

    comanda_a = await comanda_repo.create(
        restaurante_id=rest_a.id,
        numero_mesa=1,
        identificador="Mesa 01",
    )
    comanda_b = await comanda_repo.create(
        restaurante_id=rest_b.id,
        numero_mesa=1,
        identificador="Mesa 01",
    )
    await db_session.commit()

    # Inserção cross-tenant (comanda de A usando restaurante B) -> bloqueada (None)
    assert (
        await item_comanda_repo.create(
            comanda_id=comanda_a.id,
            restaurante_id=rest_b.id,
            item_id=item_b.id,
            nome_item=item_b.nome,
            quantidade=1,
            preco_unitario=item_b.preco,
        )
        is None
    )

    # Inserção legítima congelando nome e preço
    pedido_a = await item_comanda_repo.create(
        comanda_id=comanda_a.id,
        restaurante_id=rest_a.id,
        item_id=item_a.id,
        nome_item=item_a.nome,
        quantidade=2,
        preco_unitario=item_a.preco,
        observacao="Sem cebola",
    )
    pedido_b = await item_comanda_repo.create(
        comanda_id=comanda_b.id,
        restaurante_id=rest_b.id,
        item_id=item_b.id,
        nome_item=item_b.nome,
        quantidade=1,
        preco_unitario=item_b.preco,
    )
    await db_session.commit()

    assert pedido_a is not None
    assert pedido_b is not None
    assert pedido_a.nome_item == "Filé Parmegiana"
    assert pedido_a.preco_unitario == Decimal("64.90")
    assert pedido_a.status == "pendente"

    # Alterar o preço/nome do Item original no cardápio NÃO altera o registro congelado
    await item_repo.update(
        item_id=item_a.id,
        restaurante_id=rest_a.id,
        nome="Filé Parmegiana Especial",
        preco=Decimal("89.90"),
    )
    await db_session.commit()

    recarregado = await item_comanda_repo.get_by_id_and_restaurante(pedido_a.id, rest_a.id)
    assert recarregado is not None
    assert recarregado.nome_item == "Filé Parmegiana"
    assert recarregado.preco_unitario == Decimal("64.90")

    # Atualização de quantidade e observação preserva nome e preço congelados
    editado = await item_comanda_repo.update_item(
        item_comanda_id=pedido_a.id,
        restaurante_id=rest_a.id,
        quantidade=3,
        observacao="Bem passado",
        atualizar_observacao=True,
    )
    assert editado is not None
    assert editado.quantidade == 3
    assert editado.observacao == "Bem passado"
    assert editado.preco_unitario == Decimal("64.90")

    # Atualização de status e proteção IDOR
    assert (
        await item_comanda_repo.update_status(
            item_comanda_id=pedido_a.id,
            restaurante_id=rest_b.id,
            status="em_preparo",
        )
        is None
    )
    em_preparo = await item_comanda_repo.update_status(
        item_comanda_id=pedido_a.id,
        restaurante_id=rest_a.id,
        status="em_preparo",
    )
    await db_session.commit()
    assert em_preparo is not None and em_preparo.status == "em_preparo"

    # Fila KDS isolada por restaurante
    fila_a = await item_comanda_repo.list_por_status_cozinha(rest_a.id)
    assert [p.id for p in fila_a] == [pedido_a.id]
    assert fila_a[0].comanda.identificador == "Mesa 01"

    # Listagem por comanda com isolamento multi-tenant
    assert [p.id for p in await item_comanda_repo.list_by_comanda(comanda_a.id, rest_a.id)] == [pedido_a.id]
    assert await item_comanda_repo.list_by_comanda(comanda_a.id, rest_b.id) == []

    # Carregamento eager dos itens via ComandaRepository
    comanda_com_itens = await comanda_repo.get_by_id_and_restaurante(
        comanda_a.id,
        rest_a.id,
        carregar_itens=True,
    )
    assert comanda_com_itens is not None
    assert len(comanda_com_itens.itens) == 1
    assert comanda_com_itens.itens[0].id == pedido_a.id
