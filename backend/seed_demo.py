import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def seed():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("[1/6] Cadastrando Dono...")
        dono_payload = {
            "nome": "Giovanni Rossi",
            "email": "giovanni@bellanotte.com",
            "senha": "password123",
        }
        resp_cad = await client.post(f"{BASE_URL}/auth/cadastrar", json=dono_payload)
        if resp_cad.status_code == 201:
            print("Dono Giovanni Rossi cadastrado!")
        
        # Faz login via JSON
        resp_login = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": dono_payload["email"], "senha": dono_payload["senha"]},
        )
        if resp_login.status_code == 200:
            token = resp_login.json()["access_token"]
            print("Login do Dono Giovanni Rossi realizado com sucesso!")
        else:
            print(f"Erro ao autenticar Dono: {resp_login.text}")
            return

        headers = {"Authorization": f"Bearer {token}"}

        print("[2/6] Criando ou recuperando Restaurante...")
        # Listar restaurantes existentes
        resp_rests = await client.get(f"{BASE_URL}/restaurantes", headers=headers)
        restaurantes = resp_rests.json() if resp_rests.status_code == 200 else []
        rest = next((r for r in restaurantes if r.get("slug") == "bella-notte"), None)

        if not rest:
            rest_payload = {
                "nome": "Trattoria Bella Notte",
                "slug": "bella-notte",
                "codigo_garcom": "1234",
                "codigo_cozinha": "4321",
            }
            resp_create_rest = await client.post(f"{BASE_URL}/restaurantes", json=rest_payload, headers=headers)
            if resp_create_rest.status_code == 201:
                rest = resp_create_rest.json()
                print("Restaurante 'Trattoria Bella Notte' criado!")
            else:
                print(f"Erro ao criar restaurante: {resp_create_rest.text}")
                return
        else:
            print(f"Restaurante existente selecionado: {rest['nome']}")

        rest_id = rest["id"]
        headers_tenant = {"Authorization": f"Bearer {token}", "X-Restaurante-Id": rest_id}

        print("[3/6] Cadastrando Cardápio...")
        pratos = [
            {"nome": "Bruschetta Tradicional", "descricao": "Pão italiano rústico, tomate confit, manjericão fresco e azeite extravirgem", "preco": 28.0},
            {"nome": "Carpaccio di Manzo", "descricao": "Finas lâminas de mignon, molho de alcaparras, rúcula e lascas de parmesão", "preco": 44.0},
            {"nome": "Fettuccine ao Tartufo Nero", "descricao": "Massa artesanal fresca salteada na manteiga de trufas negras e queijo grana padano", "preco": 78.0},
            {"nome": "Risotto de Cogumelos Porcini", "descricao": "Arroz carnaroli italiano, cogumelos frescos e redução de vinho branco", "preco": 64.0},
            {"nome": "Bife Ancho ao Gorgonzola", "descricao": "Corte nobre grelhado na brasa servido com creme suave de queijo gorgonzola", "preco": 82.0},
            {"nome": "Pizza Margherita D.O.C.", "descricao": "Molho de tomate San Marzano, mozzarella de búfala e folhas de manjericão", "preco": 52.0},
            {"nome": "Tiramisù Clássico", "descricao": "Biscoito savoiardi embebido em café espresso, cacau puro e creme mascarpone", "preco": 28.0},
            {"nome": "Panna Cotta de Frutas Vermelhas", "descricao": "Sobremesa piemontesa sedosa com calda artesanal de amoras e framboesas", "preco": 24.0},
            {"nome": "Vinho Chianti Clássico", "descricao": "Garrafa 750ml, vinho tinto toscano encorpado safra especial", "preco": 120.0},
            {"nome": "Aperol Spritz", "descricao": "Aperol, prosecco italiano, água com gás e fatia de laranja bahia", "preco": 34.0},
            {"nome": "Água Mineral San Pellegrino", "descricao": "Garrafa de vidro 505ml com gás gaseificada na fonte", "preco": 14.0},
        ]

        itens_criados = {}
        resp_itens_existentes = await client.get(f"{BASE_URL}/itens", params={"restaurante_id": rest_id}, headers=headers_tenant)
        itens_atuais = resp_itens_existentes.json() if resp_itens_existentes.status_code == 200 else []
        mapa_atuais = {i["nome"]: i for i in itens_atuais}

        for prato in pratos:
            if prato["nome"] in mapa_atuais:
                itens_criados[prato["nome"]] = mapa_atuais[prato["nome"]]
            else:
                resp_item = await client.post(f"{BASE_URL}/itens", json=prato, params={"restaurante_id": rest_id}, headers=headers_tenant)
                if resp_item.status_code == 201:
                    itens_criados[prato["nome"]] = resp_item.json()

        print(f"Total de {len(itens_criados)} pratos disponíveis no cardápio!")

        print("[4/6] Gerando Comandas e Pedidos no Salão...")
        # Obter comandas abertas existentes
        resp_cmds = await client.get(f"{BASE_URL}/comandas", params={"restaurante_id": rest_id, "status": "aberta"}, headers=headers_tenant)
        cmds_abertas = resp_cmds.json() if resp_cmds.status_code == 200 else []
        mesas_abertas = {c.get("numero_mesa"): c for c in cmds_abertas if c.get("tipo_atendimento") == "mesa"}

        # Mesa 3
        if 3 not in mesas_abertas:
            resp_m3 = await client.post(f"{BASE_URL}/comandas", json={"tipo_atendimento": "mesa", "numero_mesa": 3}, params={"restaurante_id": rest_id}, headers=headers_tenant)
            if resp_m3.status_code == 201:
                cmd3 = resp_m3.json()
                m3_id = cmd3["id"]
                # Adicionar itens
                it1 = await client.post(f"{BASE_URL}/comandas/{m3_id}/itens", json={"item_id": itens_criados["Fettuccine ao Tartufo Nero"]["id"], "quantidade": 2, "observacao": "Ao ponto; Molho à parte"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                it2 = await client.post(f"{BASE_URL}/comandas/{m3_id}/itens", json={"item_id": itens_criados["Vinho Chianti Clássico"]["id"], "quantidade": 1, "observacao": "Trazer taças bordeaux"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                # Atualizar status no KDS
                if it1.status_code == 201:
                    await client.patch(f"{BASE_URL}/cozinha/pedidos/{it1.json()['id']}/status", json={"status": "em_preparo"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                if it2.status_code == 201:
                    await client.patch(f"{BASE_URL}/cozinha/pedidos/{it2.json()['id']}/status", json={"status": "entregue"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                print("Mesa 3 aberta com Fettuccine e Vinho!")

        # Mesa 7
        if 7 not in mesas_abertas:
            resp_m7 = await client.post(f"{BASE_URL}/comandas", json={"tipo_atendimento": "mesa", "numero_mesa": 7}, params={"restaurante_id": rest_id}, headers=headers_tenant)
            if resp_m7.status_code == 201:
                cmd7 = resp_m7.json()
                m7_id = cmd7["id"]
                it_brus = await client.post(f"{BASE_URL}/comandas/{m7_id}/itens", json={"item_id": itens_criados["Bruschetta Tradicional"]["id"], "quantidade": 1, "observacao": "Sem alho"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                it_spritz = await client.post(f"{BASE_URL}/comandas/{m7_id}/itens", json={"item_id": itens_criados["Aperol Spritz"]["id"], "quantidade": 2, "observacao": "Gelo e limão"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                if it_spritz.status_code == 201:
                    await client.patch(f"{BASE_URL}/cozinha/pedidos/{it_spritz.json()['id']}/status", json={"status": "pronto"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                print("Mesa 7 aberta com Bruschetta e Aperol Spritz!")

        # Mesa 12
        if 12 not in mesas_abertas:
            resp_m12 = await client.post(f"{BASE_URL}/comandas", json={"tipo_atendimento": "mesa", "numero_mesa": 12}, params={"restaurante_id": rest_id}, headers=headers_tenant)
            if resp_m12.status_code == 201:
                cmd12 = resp_m12.json()
                m12_id = cmd12["id"]
                it_bife = await client.post(f"{BASE_URL}/comandas/{m12_id}/itens", json={"item_id": itens_criados["Bife Ancho ao Gorgonzola"]["id"], "quantidade": 2, "observacao": "Ao ponto mais"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                it_pizza = await client.post(f"{BASE_URL}/comandas/{m12_id}/itens", json={"item_id": itens_criados["Pizza Margherita D.O.C."]["id"], "quantidade": 1, "observacao": "Massa fina"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                it_tira = await client.post(f"{BASE_URL}/comandas/{m12_id}/itens", json={"item_id": itens_criados["Tiramisù Clássico"]["id"], "quantidade": 2, "observacao": None}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                if it_bife.status_code == 201:
                    await client.patch(f"{BASE_URL}/cozinha/pedidos/{it_bife.json()['id']}/status", json={"status": "em_preparo"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                if it_tira.status_code == 201:
                    await client.patch(f"{BASE_URL}/cozinha/pedidos/{it_tira.json()['id']}/status", json={"status": "pronto"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                print("Mesa 12 aberta com Bife Ancho, Pizza e Tiramisù!")

        # Balcão / Viagem
        cmd_viagem = next((c for c in cmds_abertas if c.get("tipo_atendimento") != "mesa"), None)
        if not cmd_viagem:
            resp_vg = await client.post(f"{BASE_URL}/comandas", json={"tipo_atendimento": "viagem", "identificador": "Carlos M. (Viagem)"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
            if resp_vg.status_code == 201:
                cvg = resp_vg.json()
                cvg_id = cvg["id"]
                await client.post(f"{BASE_URL}/comandas/{cvg_id}/itens", json={"item_id": itens_criados["Pizza Margherita D.O.C."]["id"], "quantidade": 1, "observacao": "Para viagem bem embalada"}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                await client.post(f"{BASE_URL}/comandas/{cvg_id}/itens", json={"item_id": itens_criados["Panna Cotta de Frutas Vermelhas"]["id"], "quantidade": 1, "observacao": None}, params={"restaurante_id": rest_id}, headers=headers_tenant)
                print("Pedido de Viagem de Carlos M. criado!")

        print("[5/6] Cadastrando Despesas Operacionais...")
        despesas_iniciais = [
            {"descricao": "Fornecedor de Queijos & Frios Artesanais", "categoria": "insumos", "valor": 3800.0, "data_pagamento": "2026-11-18"},
            {"descricao": "Conta de Energia Elétrica (CPFL)", "categoria": "contas_fixas", "valor": 1650.0, "data_pagamento": "2026-11-15"},
            {"descricao": "Manutenção Preventiva Forno de Pizza", "categoria": "manutencao", "valor": 760.0, "data_pagamento": "2026-11-10"},
        ]
        resp_desp_existentes = await client.get(f"{BASE_URL}/financeiro/despesas", params={"restaurante_id": rest_id}, headers=headers_tenant)
        desp_existentes = resp_desp_existentes.json() if resp_desp_existentes.status_code == 200 else []
        desc_existentes = {d["descricao"] for d in desp_existentes}

        for desp in despesas_iniciais:
            if desp["descricao"] not in desc_existentes:
                await client.post(f"{BASE_URL}/financeiro/despesas", json=desp, params={"restaurante_id": rest_id}, headers=headers_tenant)
        print("Despesas operacionais sincronizadas!")

        print("[6/6] Semente concluída com sucesso! 'Trattoria Bella Notte' está pronta para as capturas.")

if __name__ == "__main__":
    asyncio.run(seed())
