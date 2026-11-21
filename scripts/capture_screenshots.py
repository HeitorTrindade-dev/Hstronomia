import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5173"
OUTPUT_DIR = "assets/screenshots"

os.makedirs(OUTPUT_DIR, exist_ok=True)

async def capture():
    async with async_playwright() as p:
        # Configurar navegador headless
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )

        # -------------------------------------------------------------
        # CENA 6: Acesso Operacional por PIN (Keypad Touch)
        # -------------------------------------------------------------
        print("[1/6] Capturando Cena 6: Acesso Operacional por PIN...")
        ctx_mobile = await browser.new_context(
            viewport={"width": 430, "height": 880},
            device_scale_factor=2,
        )
        page_pin = await ctx_mobile.new_page()
        await page_pin.goto(f"{BASE_URL}/acesso/bella-notte", wait_until="networkidle")
        await page_pin.wait_for_timeout(1000)

        # Simular digitacao parcial de 2 digitos para demonstrar os pontinhos ativos
        key_1 = page_pin.locator("button:has-text('1')").first
        key_2 = page_pin.locator("button:has-text('2')").first
        if await key_1.count() > 0:
            await key_1.click()
            await page_pin.wait_for_timeout(300)
            await key_2.click()
            await page_pin.wait_for_timeout(500)

        await page_pin.screenshot(path=f"{OUTPUT_DIR}/06-acesso-pin.png")
        print("Salvo: 06-acesso-pin.png")
        await ctx_mobile.close()

        # -------------------------------------------------------------
        # CENA 1: Salão & Mesas em Tempo Real (Terminal do Garçom)
        # -------------------------------------------------------------
        print("[2/6] Capturando Cena 1: Salão & Mesas em Tempo Real...")
        ctx_garcom = await browser.new_context(
            viewport={"width": 430, "height": 900},
            device_scale_factor=2,
        )
        page_garcom = await ctx_garcom.new_page()
        await page_garcom.goto(f"{BASE_URL}/acesso/bella-notte", wait_until="networkidle")
        await page_garcom.wait_for_timeout(800)

        # Selecionar 'Garçom'
        btn_garcom_sel = page_garcom.locator("button:has-text('Garçom')").first
        if await btn_garcom_sel.count() > 0:
            await btn_garcom_sel.click()
            await page_garcom.wait_for_timeout(200)

        # Digitar PIN 1234
        for digit in ["1", "2", "3", "4"]:
            btn = page_garcom.locator(f"button:text-is('{digit}')").first
            await btn.click()
            await page_garcom.wait_for_timeout(150)

        # Clicar no botão Confirmar PIN
        btn_confirm = page_garcom.locator("button[aria-label='Confirmar PIN']").first
        await btn_confirm.click()

        await page_garcom.wait_for_url("**/garcom/**", timeout=10000)
        await page_garcom.wait_for_timeout(1500)
        await page_garcom.screenshot(path=f"{OUTPUT_DIR}/01-salao-mesas.png")
        print("Salvo: 01-salao-mesas.png")

        # -------------------------------------------------------------
        # CENA 2: Lançamento de Pedidos com Observações Rápidas
        # -------------------------------------------------------------
        print("[3/6] Capturando Cena 2: Lançamento de Pedidos...")
        # Clicar na Mesa 3 para ver os detalhes
        mesa_3 = page_garcom.locator("button:has-text('Mesa 3')").first
        if await mesa_3.count() > 0:
            await mesa_3.click()
            await page_garcom.wait_for_url("**/garcom/comandas/**", timeout=8000)
            await page_garcom.wait_for_timeout(1000)

            # Clicar no botão 'Lançar Itens'
            btn_add = page_garcom.locator("button:has-text('Lançar Itens')").first
            if await btn_add.count() > 0:
                await btn_add.click()
                await page_garcom.wait_for_timeout(1000)

                # Selecionar o Fettuccine para mostrar o seletor táctil e chips
                fettuccine_btn = page_garcom.locator("dialog[open] button:has-text('Fettuccine ao Tartufo Nero')").first
                if await fettuccine_btn.count() > 0:
                    await fettuccine_btn.click()
                    await page_garcom.wait_for_timeout(600)

                    # Aumentar quantidade para 2x usando o botão plus DENTRO do dialog
                    btn_plus = page_garcom.locator("dialog[open] button:has(svg.lucide-plus)").first
                    if await btn_plus.count() > 0:
                        await btn_plus.click()

                    # Clicar nos chips de observacao dentro do dialog
                    chip_ponto = page_garcom.locator("dialog[open] button:has-text('Ao ponto')").first
                    chip_molho = page_garcom.locator("dialog[open] button:has-text('Molho à parte')").first
                    if await chip_ponto.count() > 0:
                        await chip_ponto.click()
                    if await chip_molho.count() > 0:
                        await chip_molho.click()

                    # Preencher observacao livre
                    obs_input = page_garcom.locator("dialog[open] input[placeholder*='sem pimenta']").first
                    if await obs_input.count() > 0:
                        await obs_input.fill("Dividir em 2 pratos; queijo extra")

                    await page_garcom.wait_for_timeout(500)
                    await page_garcom.screenshot(path=f"{OUTPUT_DIR}/02-lancamento-pedido.png")
                    print("Salvo: 02-lancamento-pedido.png")

        # -------------------------------------------------------------
        # CENA 3: Prévia e Fechamento de Conta (Caixa)
        # -------------------------------------------------------------
        print("[4/6] Capturando Cena 3: Fechamento de Conta...")
        # Fechar o modal de adicao se ainda aberto
        btn_close_modal = page_garcom.locator("dialog[open] button:has(svg.lucide-x)").first
        if await btn_close_modal.count() > 0:
            await btn_close_modal.click()
            await page_garcom.wait_for_timeout(500)
        else:
            await page_garcom.keyboard.press("Escape")
            await page_garcom.wait_for_timeout(500)

        btn_fechar_conta = page_garcom.locator("button:has-text('Fechar Conta')").first
        if await btn_fechar_conta.count() > 0:
            await btn_fechar_conta.click()
            await page_garcom.wait_for_timeout(1200)

            # Clicar em 'Dinheiro' dentro do modal
            btn_dinheiro = page_garcom.locator("dialog[open] button:has-text('Dinheiro')").first
            if await btn_dinheiro.count() > 0:
                await btn_dinheiro.click()
                await page_garcom.wait_for_timeout(400)

                # Preencher valor recebido para calcular troco
                input_dinheiro = page_garcom.locator("dialog[open] input[placeholder*='50,00']").first
                if await input_dinheiro.count() > 0:
                    await input_dinheiro.fill("300")
                    await page_garcom.wait_for_timeout(500)

            await page_garcom.screenshot(path=f"{OUTPUT_DIR}/03-fechamento-conta.png")
            print("Salvo: 03-fechamento-conta.png")

        await ctx_garcom.close()

        # -------------------------------------------------------------
        # CENA 4: Cozinha KDS em Tempo Real (Dark Mode)
        # -------------------------------------------------------------
        print("[5/6] Capturando Cena 4: Cozinha KDS...")
        ctx_kds = await browser.new_context(
            viewport={"width": 1280, "height": 780},
            device_scale_factor=2,
        )
        page_kds = await ctx_kds.new_page()
        await page_kds.goto(f"{BASE_URL}/acesso/bella-notte", wait_until="networkidle")
        await page_kds.wait_for_timeout(800)

        # Selecionar 'Cozinha'
        btn_cozinha_sel = page_kds.locator("button:has-text('Cozinha')").first
        if await btn_cozinha_sel.count() > 0:
            await btn_cozinha_sel.click()
            await page_kds.wait_for_timeout(200)

        # Digitar PIN 4321
        for digit in ["4", "3", "2", "1"]:
            btn = page_kds.locator(f"button:text-is('{digit}')").first
            await btn.click()
            await page_kds.wait_for_timeout(150)

        # Clicar no botão Confirmar PIN
        btn_confirm_kds = page_kds.locator("button[aria-label='Confirmar PIN']").first
        await btn_confirm_kds.click()

        await page_kds.wait_for_url("**/cozinha**", timeout=10000)
        await page_kds.wait_for_timeout(1500)
        await page_kds.screenshot(path=f"{OUTPUT_DIR}/04-cozinha-kds.png")
        print("Salvo: 04-cozinha-kds.png")
        await ctx_kds.close()

        # -------------------------------------------------------------
        # CENA 5: Painel Financeiro do Dono (KPIs & Despesas)
        # -------------------------------------------------------------
        print("[6/6] Capturando Cena 5: Painel Financeiro do Dono...")
        ctx_dono = await browser.new_context(
            viewport={"width": 1280, "height": 840},
            device_scale_factor=2,
        )
        page_dono = await ctx_dono.new_page()
        await page_dono.goto(f"{BASE_URL}/login", wait_until="networkidle")

        # Fazer login do Dono
        await page_dono.fill("input[type='email']", "giovanni@bellanotte.com")
        await page_dono.fill("input[type='password']", "password123")
        await page_dono.click("button[type='submit']")
        await page_dono.wait_for_url("**/admin**", timeout=10000)
        await page_dono.wait_for_timeout(1000)

        # Acessar a página Financeira
        await page_dono.goto(f"{BASE_URL}/admin/financeiro", wait_until="networkidle")
        await page_dono.wait_for_timeout(1500)

        # Garantir seleção da Trattoria Bella Notte no TopBar se houver seletor
        select_rest = page_dono.locator("select[aria-label='Selecionar restaurante ativo']").first
        if await select_rest.count() > 0:
            await select_rest.select_option(label="Trattoria Bella Notte")
            await page_dono.wait_for_timeout(1000)

        # Selecionar período 'Este Mês'
        btn_mes = page_dono.locator("button:has-text('Este Mês')").first
        if await btn_mes.count() > 0:
            await btn_mes.click()
            await page_dono.wait_for_timeout(1000)

        await page_dono.screenshot(path=f"{OUTPUT_DIR}/05-painel-financeiro.png")
        print("Salvo: 05-painel-financeiro.png")
        await ctx_dono.close()

        await browser.close()
        print("\nTodas as 6 capturas foram geradas com sucesso em assets/screenshots/!")

if __name__ == "__main__":
    asyncio.run(capture())
