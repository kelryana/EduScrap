##take_screenshots.py
"""Tira screenshots do dashboard em Chromium headless via Playwright (navegador real)."""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1440, "height": 960}, device_scale_factor=2)

    # Sessão fake para o frontend não redirecionar para login
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script("""
        localStorage.setItem('eduscrap_token', 'preview-token');
        localStorage.setItem('eduscrap_user', JSON.stringify({id:'preview', nome:'Ana Estudante', email:'ana@uern.br', papel:'estudante'}));
    """)
    page.goto(BASE + "/index.html", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)

    # Home (grade de cards) — tema claro
    page.screenshot(path="shots/01_home_claro.png", full_page=False)

    # Abrir a aba Analises (dashboard de indicadores)
    page.click("#btn-analises")
    page.wait_for_selector(".dash-kpi-card", timeout=30000)
    page.wait_for_timeout(2500)  # deixar animacoes de entrada/count-up terminarem

    page.screenshot(path="shots/02_dashboard_topo_claro.png")

    # Scroll até o gráfico de fluxo / donuts
    page.evaluate("window.scrollTo(0, 700)")
    page.wait_for_timeout(600)
    page.screenshot(path="shots/03_dashboard_meio_claro.png")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.screenshot(path="shots/04_dashboard_rodape_claro.png")

    # Página inteira do dashboard
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)
    page.screenshot(path="shots/05_dashboard_pagina_inteira_claro.png", full_page=True)

    # Tema escuro
    page.evaluate("""() => {
        if (typeof aplicarTema === 'function') aplicarTema('dark');
        else document.documentElement.classList.add('dark');
        localStorage.setItem('eduscrap_tema','dark');
    }""")
    page.wait_for_timeout(1200)
    page.screenshot(path="shots/06_dashboard_topo_escuro.png")
    page.evaluate("window.scrollTo(0, 700)")
    page.wait_for_timeout(600)
    page.screenshot(path="shots/07_dashboard_meio_escuro.png")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(800)
    page.screenshot(path="shots/08_dashboard_rodape_escuro.png")

    print("Erros de JS na pagina:", errors if errors else "nenhum")
    browser.close()
print("OK")
