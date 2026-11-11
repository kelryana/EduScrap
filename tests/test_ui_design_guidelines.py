# -*- coding: utf-8 -*-
"""
Suite de Validação Automatizada de Diretrizes de Interface (Frontend) e Regras de Ouro de Ben Shneiderman.
Valida:
1. Taste Skill & Awesome Design (Design Tokens, Neobrutalismo, Phosphor Icons)
2. Web Design Guidelines (Semântica HTML5, WCAG, estados focus-visible e disabled)
3. As 8 Regras de Ouro de Ben Shneiderman em index.html, login.html, admin.html, script.js e style.css
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def _read(filename: str) -> str:
    return (FRONTEND_DIR / filename).read_text(encoding="utf-8")


def test_regra_1_consistencia_e_tokens_neobrutalistas():
    """Regra 1 (Buscar Consistência) + Taste Skill + Awesome Design."""
    style_css = _read("style.css")
    index_html = _read("index.html")
    login_html = _read("login.html")
    admin_html = _read("admin.html")

    # Design Tokens e paleta oficial presentes
    assert "#FF5C00" in style_css or "#FF7A00" in style_css
    assert "#0F172A" in style_css
    assert "#FACC15" in style_css

    # Uso consistente de Phosphor Icons e suporte a tema claro/escuro nas 3 páginas
    for html in (index_html, login_html, admin_html):
        assert "@phosphor-icons/web" in html
        assert "theme.js" in html
        assert "toggleTheme()" in html


def test_web_design_guidelines_semantica_e_focus_visible():
    """Web Design Guidelines (skills.sh): Semântica HTML5 e estados interativos :focus-visible / :disabled."""
    style_css = _read("style.css")
    index_html = _read("index.html")
    login_html = _read("login.html")
    admin_html = _read("admin.html")

    # Semântica obrigatória
    assert "<main" in index_html and "<nav" in index_html and "<footer" in index_html
    assert "<main" in login_html and "<header" in login_html
    assert "<main" in admin_html and "<header" in admin_html and "<section" in admin_html

    # Estados de foco visível e desabilitado explícitos no CSS
    assert ":focus-visible" in style_css
    assert "button:disabled" in style_css


def test_regra_2_atalhos_para_usuarios_frequentes():
    """Regra 2 (Atalhos para Usuários Frequentes): '/', 'Ctrl+K', 'Enter', 'Escape'."""
    index_html = _read("index.html")
    script_js = _read("script.js")
    admin_html = _read("admin.html")

    # Atalho '/' indicado na barra de busca e tratado no script.js
    assert 'id="busca-kbd-hint"' in index_html
    assert "event.key === '/'" in script_js
    assert "event.key === 'Escape'" in script_js
    assert "event.key === 'Enter'" in index_html
    assert 'event.key === "Escape"' in admin_html


def test_regra_3_e_4_feedback_informativo_e_fechamento_de_fluxos():
    """Regra 3 (Feedback Informativo) & Regra 4 (Diálogos que Fechem Fluxos)."""
    script_js = _read("script.js")
    login_html = _read("login.html")
    admin_html = _read("admin.html")

    # Skeletons e Toasts em script.js
    assert "function renderizarSkeletons" in script_js
    assert "function renderizarSkeletonDashboard" in script_js
    assert "function mostrarToast" in script_js

    # Feedback de carregamento e conclusão no login/cadastro e no admin
    assert "Verificando credenciais..." in login_html
    assert "Sucesso! Redirecionando..." in login_html
    assert "Conta criada! Redirecionando..." in login_html
    assert "Atualizando..." in admin_html
    assert "Expurgando..." in admin_html


def test_regra_5_prevencao_e_tratamento_simples_de_erros():
    """Regra 5 (Prevenção de Erros): Validação em tempo real de senha/email e Estado de Erro Amigável."""
    script_js = _read("script.js")
    login_html = _read("login.html")

    assert "function verificarRequisitosSenha" in login_html
    assert "function verificarDisponibilidadeEmail" in login_html
    assert "function renderizarEstadoErro" in script_js
    assert "Tentar Novamente" in script_js


def test_regra_6_reversao_facil_de_acoes_undo():
    """Regra 6 (Permitir Reversão Fácil de Ações - Undo): Limpar Busca, Banner Desfazer Filtro, Limpar Chips."""
    index_html = _read("index.html")
    login_html = _read("login.html")
    script_js = _read("script.js")

    # Limpar busca e banner de filtro ativo com botão Desfazer
    assert 'id="btn-limpar-busca"' in index_html
    assert 'id="banner-filtro-ativo"' in index_html
    assert "Desfazer / Limpar Filtro" in index_html
    assert "function atualizarBannerFiltroAtivo" in script_js

    # Limpar seleção de chips no cadastro, sidebar e portal
    assert "function limparSelecaoChips" in script_js
    assert "function limparSelecaoChipsCadastro" in login_html


def test_regra_7_e_8_controle_interno_e_reducao_carga_memoria():
    """Regra 7 (Controle Interno) & Regra 8 (Reduzir Carga de Memória de Curto Prazo)."""
    index_html = _read("index.html")
    script_js = _read("script.js")

    # Prazos críticos fixados no topo e soma matemática exata das 8 categorias no dashboard
    assert 'id="painel-prazos-criticos"' in index_html
    assert "somaCategorias = totalEstagios + totalBolsas + totalUfersa + totalCursosBolsas + totalTech + totalUern + totalDom + totalIfrn" in script_js
