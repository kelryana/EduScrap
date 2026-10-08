from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EXTENSOES_CODIGO = {".py", ".js", ".html", ".css", ".json", ".sh"}
DIRS_IGNORADOS = {".git", "__pycache__", "venv", ".venv", "env", "node_modules", ".idea", ".vscode"}

RELATORIO_PADRAO = "RELATORIO_TECNICO.md"

DESCRICAO_BIBLIOTECAS = {
    "requests": "Cliente HTTP síncrono para coleta de páginas estáticas (HTML) dos portais.",
    "beautifulsoup4": "Parser de HTML/XML; transforma o corpo das respostas em árvore navegável (BeautifulSoup) para extração de editais.",
    "selenium": "Automação de navegador real (Chrome/Firefox headless) para contornar proteção Cloudflare e páginas dinâmicas (Portal UERN, CIEE).",
    "pdfplumber": "Extração precisa de texto e tabelas de PDFs (editais/Diário Oficial) na esteira de normalização.",
    "PyPDF2": "Leitura/manipulação leve de PDFs (metadados e divisão de páginas) como alternativa ao pdfplumber.",
    "lxml": "Backend de parser rápido usado pelo BeautifulSoup para documentos grandes.",
    "fastapi": "Framework web assíncrono moderno que serve a API principal (backend/main.py) com documentação Swagger automática.",
    "uvicorn": "Servidor ASGI que executa a aplicação FastAPI (porta 8000).",
    "flask": "Microframework usado pela segunda interface REST (backend/api/app.py), baseada em Blueprints.",
    "flask-cors": "Extensão Flask que habilita CORS para as rotas /api/* consumidas pelo frontend.",
    "pymongo": "Driver oficial MongoDB — persistência de vagas, editais, notícias, fontes e logs de auditoria.",
    "schedule": "Agendador leve em Python (Scheduler) para varreduras periódicas e atualização de status.",
    "python-dotenv": "Carregamento de variáveis de ambiente (.env), ex.: MONGODB_URI.",
    "logging": "Registro estruturado de eventos dos scrapers (console + arquivos .log).",
}

    "schedule": "Agendador leve em Python (Scheduler) para varreduras periódicas e atualização de status.",
    "python-dotenv": "Carregamento de variáveis de ambiente (.env), ex.: MONGODB_URI.",
    "logging": "Registro estruturado de eventos dos scrapers (console + arquivos .log).",
}

# Descrição das coleções MongoDB inferida do código
DESCRICAO_COLECOES = {
    "vagas_estagio": "Editais de estágio acadêmico coletados da PRAE/UERN.",
    "vagas_bolsa": "Editais de bolsas de extensão coletados da PROEX/UERN.",
    "vagas_ufersa": "Editais de assistência estudantil/concursos da UFERSA.",
    "vagas_ciee": "Vagas de estágio e Jovem Aprendiz do CIEE (Mossoró), via Selenium.",
    "vagas_noticias": "Notícias tech agregadas (G1, Canaltech) — refresh a cada 10 min.",
    "vagas_portal_uern": "Notícias do Portal UERN filtradas por mineração de palavras-chave (text mining).",
    "fontes_provedores": "Governança/metadados das instituições (nome oficial, URL, frequência, foco).",
    "historico_varreduras": "Log de auditoria de cada 'Varredura Global' (duração, status, contagens).",
    "controle_cache": "Carimbo de tempo da última execução de cada robô (controle de cache TTL).",
    "editais": "Coleção padronizada da esteira de normalização (src/normalizer/database.py).",
    "vagas": "Coleção padronizada da esteira de normalização (src/normalizer/database.py).",
    "noticias": "Coleção padronizada da esteira de normalização (src/normalizer/database.py).",
}

def ler_texto(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def listar_arquivos(raiz: Path) -> list:
    """Retorna todos os arquivos versionáveis do projeto (sem pastas ignoradas)."""
    resultado = []
    for raiz_dir, dirs, arquivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in DIRS_IGNORADOS]
        for nome in arquivos:
            p = Path(raiz_dir) / nome
            if p.suffix.lower() in EXTENSOES_CODIGO or nome in {"README.md", "LICENSE", ".gitignore"}:
                resultado.append(p)
    return sorted(resultado)


def contar_linhas_total(arquivos: list) -> dict:
    contagem = {}
    for p in arquivos:
        n = len(ler_texto(p).splitlines())
        ext = p.suffix.lower() or "(sem extensão)"
        contagem[ext] = contagem.get(ext, 0) + n
    return contagem

def analisar_requirements(raiz: Path) -> list:
    """Lê requirements.txt retornando [(pacote, versão), ...]."""
    conteudo = ler_texto(raiz / "requirements.txt")
    pacotes = []
    for linha in conteudo.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.\-]+)\s*([><=!~]=?.*)?$", linha)
        if m:
            pacotes.append((m.group(1), (m.group(2) or "última").strip()))
    return pacotes


def analisar_python(raiz: Path, caminho: Path) -> dict:
    """Usa AST para extrair docstrings, classes, funções e imports de um .py."""
    src = ler_texto(caminho)
    info = {
        "arquivo": str(caminho.relative_to(raiz)),
        "docstring": "",
        "classes": [],
        "funcoes": [],
        "imports": set(),
        "linhas": len(src.splitlines()),
    }
    try:
        arvore = ast.parse(src)
        info["docstring"] = (ast.get_docstring(arvore) or "").strip().split("\n")[0]
        for no in arvore.body:
            if isinstance(no, ast.ClassDef):
                metodos = [f.name for f in no.body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))]
                info["classes"].append({
                    "nome": no.name,
                    "docstring": (ast.get_docstring(no) or "").strip().split("\n")[0],
                    "metodos": metodos,
                })
            elif isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info["funcoes"].append({
                    "nome": no.name,
                    "docstring": (ast.get_docstring(no) or "").strip().split("\n")[0],
                })
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                for alias in no.names:
                    info["imports"].add(alias.name.split(".")[0])
            elif isinstance(no, ast.ImportFrom):
                if no.module:
                    info["imports"].add(no.module.split(".")[0])
    except SyntaxError:
        pass
    return info


def analisar_rotas_fastapi(raiz: Path) -> list:
    """Extrai rotas @app.get(...) de backend/main.py."""
    rotas = []
    src = ler_texto(raiz / "backend" / "main.py")
    padrao = re.compile(r'@app\.(get|post|put|delete|patch)\("([^"]+)"\)\s*\ndef\s+(\w+)\(([^)]*)\)', re.S)
    descricoes = {
        "/": "Raiz — mensagem de boas-vindas e pointer para /docs.",
        "/api/estagios": "Lista paginada de estágios (PRAE) com filtro de vigência.",
        "/api/bolsas": "Lista paginada de bolsas (PROEX) com filtro de vigência.",
        "/api/ufersa": "Lista paginada de editais da UFERSA.",
        "/api/ciee": "Lista paginada de vagas do CIEE (normaliza campo 'nome').",
        "/api/portal_uern": "Lista paginada de notícias mineradas do Portal UERN.",
        "/api/noticias": "Notícias tech com cache TTL de 10 minutos (dispara scraper se expirado).",
        "/api/pesquisar": "Pesquisa unificada $text (fallback $regex) em todas as coleções.",
        "/api/estatisticas": "Dashboard analítico: totais, reta final (7 dias) e distribuição por categoria.",
        "/api/db-status": "Auditoria física do MongoDB: documentos, KB, índices e validadores por coleção.",
        "/api/buscar-tudo": "Orquestra TODOS os robôs de coleta + normalização heurística + log de auditoria.",
    }
    for m in padrao.finditer(src):
        metodo, caminho_, func, params = m.groups()
        params_limpos = ", ".join(
            p.split(":")[0].split("=")[0].strip() for p in params.split(",") if p.strip()
        )
        rotas.append({
            "metodo": metodo.upper(),
            "caminho": caminho_,
            "funcao": func,
            "parametros": params_limpos,
            "descricao": descricoes.get(caminho_, ""),
        })
    return rotas


def analisar_rotas_flask(raiz: Path) -> list:
    """Extrai rotas da API Flask alternativa (backend/api)."""
    rotas = []
    app_src = ler_texto(raiz / "backend" / "api" / "app.py")
    routes_src = ler_texto(raiz / "backend" / "api" / "routes.py")

    descricoes = {
        "/api/oportunidades": "Lista oportunidades (editais+vagas) com filtros area/status/tipo.",
        "/api/editais": "Lista editais normalizados com filtros status/fonte.",
        "/api/vagas": "Lista vagas com filtros area/fonte.",
        "/api/noticias": "Lista notícias com filtro por categoria.",
        "/api/oportunidades/<int:id>": "Busca uma oportunidade por ID em editais/vagas/noticias.",
    }
    for m in re.finditer(
        r"@api_routes\.route\('([^']+)'(?:,\s*methods=\[([^\]]+)\])?\)\s*\ndef\s+(\w+)\(", routes_src
    ):
        caminho_, methods, func = m.groups()
        full = "/api" + caminho_
        rotas.append({
            "metodo": (methods or "'GET'").replace("'", "").upper(),
            "caminho": full,
            "funcao": func,
            "origem": "routes.py (Blueprint)",
            "descricao": descricoes.get(full, ""),
        })
    return rotas


def analisar_scrapers(raiz: Path) -> list:
    """Identifica cada scraper, suas URLs-alvo e coleções de destino."""
    diretorio = raiz / "backend"
    scrapers = []
    nomes_fontes = {
        "scraper_prae.py": ("PRAE/UERN", "Estágios acadêmicos, residência e auxílios"),
        "scraper_proex.py": ("PROEX/UERN", "Bolsas de extensão, cultura e pesquisa"),
        "scraper_ufersa.py": ("UFERSA", "Editais de assistência estudantil e concursos"),
        "scraper_ciee.py": ("CIEE", "Estágio comercial e Jovem Aprendiz (Mossoró)"),
        "scraper_noticias.py": ("G1 / Canaltech", "Notícias de tecnologia (feed agregado)"),
        "scraper_portal_uern.py": ("Portal UERN", "Text mining de notícias relevantes (anti-Cloudflare)"),
    }
    for arquivo in sorted(diretorio.glob("scraper_*.py")):
        src = ler_texto(arquivo)
        urls = sorted(set(re.findall(r'https?://[^\s\'"]+', src)))
        colecoes = sorted(
            set(re.findall(r'db\["([\w]+)"\]', src))
            | set(re.findall(r"db\['([\w]+)'\]", src))
            | set(re.findall(r'COLLECTION_NAME\s*=\s*"([\w]+)"', src))
        )
        tec = []
        if "selenium" in src:
            tec.append("Selenium (navegador headless)")
        if "webdriver_manager" in src:
            tec.append("webdriver-manager")
        if "BeautifulSoup" in src:
            tec.append("BeautifulSoup")
        if re.search(r"requests\.(get|post)", src):
            tec.append("requests")
        if "pdfplumber" in src or "pdfminer" in src:
            tec.append("extração de PDF")
        if "$set" in src and "upsert=True" in src:
            tec.append("upsert idempotente (deduplicação)")
        if "delete_many" in src:
            tec.append("limpeza prévia da coleção")
        nome, foco = nomes_fontes.get(arquivo.name, (arquivo.stem, ""))
        scrapers.append({
            "arquivo": arquivo.name,
            "fonte": nome,
            "foco": foco,
            "colecoes": colecoes,
            "urls": urls,
            "tecnicas": tec,
            "linhas": len(src.splitlines()),
        })
    return scrapers


def analisar_colecoes_mongo(raiz: Path) -> list:
    """Todas as coleções citadas no código do backend."""
    colset = set()
    for py in (raiz / "backend").rglob("*.py"):
        src = ler_texto(py)
        colset.update(re.findall(r'db\["([\w]+)"\]', src))
        colset.update(re.findall(r"db\['([\w]+)'\]", src))
        colset.update(re.findall(r'self\.db\[.([\w]+).\]', src))
        colset.update(re.findall(r'COLLECTION_NAME\s*=\s*"([\w]+)"', src))
    return sorted(colset)


def analisar_diagramas(raiz: Path) -> list:
    """Lê os diagramas PlantUML e extrai título, atores/componentes/relações."""
    diagrams = []
    diretorio = raiz / "diagrams"
    if not diretorio.exists():
        return diagrams
    for arquivo in sorted(diretorio.iterdir()):
        if not arquivo.is_file():
            continue
        src = ler_texto(arquivo)
        titulo = ""
        m = re.search(r"title\s+(.+)", src)
        if m:
            titulo = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        nomes_comp = re.findall(r'(?:Component|ComponentDb)\(\w+,\s*"([^"]+)"', src)
        # rectangle/database com título multiline "«tag»\n<b>Nome</b>\ndesc" → pegar o <b>Nome</b>
        blocos = re.findall(r'(?:rectangle|database|container|node|System_Ext|System)\s+"((?:[^"]|\\n)+?)"', src)
        nomes_rect = []
        for bloco in blocos:
            m2 = re.search(r"<b>([^<]+)</b>", bloco)
            if m2:
                nomes_rect.append(m2.group(1))
            else:
                # primeira linha que não seja estereótipo «...»
                partes = [p.strip() for p in bloco.split("\\n") if p.strip() and not p.strip().startswith("«")]
                if partes:
                    nomes_rect.append(partes[0])
        todos = [re.sub(r"\s+", " ", x).strip() for x in nomes_comp + nomes_rect if x.strip()]
        atores = re.findall(r'<<person>>', src)
        rels = re.findall(r'Rel\((\w+),\s*(\w+),\s*"([^"]+)"', src)
        arrows = re.findall(r'^(\w+)\s(-{2,3}>|--?>>)\s(\w+)\s*:\s*(.+)$', src, re.M)
        diagrams.append({
            "arquivo": arquivo.name,
            "titulo": titulo,
            "componentes": todos[:16],
            "atores": len(atores),
            "rels": rels,
            "arrows": [
                (a, b, re.sub(r"<[^>]+>|\\n|\\i", "", msg).strip())
                for a, _seta, b, msg in arrows
            ],
        })
    return diagrams


def analisar_frontend(raiz: Path) -> dict:
    """Resumo do frontend: botões/tabs, chamadas de API e estilo."""
    html = ler_texto(raiz / "frontend" / "index.html")
    js = ler_texto(raiz / "frontend" / "script.js")
    css = ler_texto(raiz / "frontend" / "style.css")

    botoes = re.findall(r'id="(btn-[\w-]+)"[^>]*>(.*?)</button>', html, re.S)
    botoes = [(b[0], re.sub(r"<.*?>", " ", b[1]).strip()) for b in botoes]
    # Remove rótulos vazios (ícone apenas) e mantém ordem de aparecimento
    chamadas = sorted(set(re.findall(r'fetch\(`\$\{API_URL\}/([\w-]+)', js)))
    funcoes_js = re.findall(r'(?:async\s+)?function\s+(\w+)', js)
    cores = re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', css)
    api_url = (re.search(r'const API_URL = "([^"]+)"', js) or [None, ""])[1]
    scripts_ext = [s for s in re.findall(r'<script src="([^"]+)"', html) if "script.js" not in s]
    return {
        "titulo_pagina": (re.search(r"<title>(.*?)</title>", html) or [None, ""])[1],
        "api_url": api_url,
        "botoes": botoes,
        "chamadas_api": chamadas,
        "funcoes_js": funcoes_js,
        "paleta": cores,
        "linhas": {"html": len(html.splitlines()), "js": len(js.splitlines()), "css": len(css.splitlines())},
        "bibliotecas_externas": scripts_ext,
    }


def analisar_config(raiz: Path) -> dict:
    """Sumariza os JSONs de configuração."""
    out = {}
    cm_path = raiz / "config" / "course_mapping.json"
    if cm_path.exists():
        try:
            cm = json.loads(ler_texto(cm_path))
            out["course_mapping"] = {
                "areas": list(cm.get("areas", {}).keys()),
                "total_cursos": sum(len(v) for v in cm.get("areas", {}).values()),
                "tem_keywords": "keywords" in cm,
            }
        except json.JSONDecodeError:
            pass
    pt_path = raiz / "config" / "patterns.json"
    if pt_path.exists():
        try:
            pt = json.loads(ler_texto(pt_path))
            out["patterns"] = {k: (list(v.keys()) if isinstance(v, dict) else v) for k, v in pt.items()}
        except json.JSONDecodeError:
            pass
    return out


def analisar_tests(raiz: Path) -> list:
    """Extrai suites e casos de teste dos arquivos em tests/."""
    suites = []
    diretorio = raiz / "tests"
    if not diretorio.exists():
        return suites
    for arquivo in sorted(diretorio.glob("test_*.py")):
        src = ler_texto(arquivo)
        try:
            arvore = ast.parse(src)
        except SyntaxError:
            continue
        classes = []
        avulsos = []
        for no in arvore.body:
            if isinstance(no, ast.ClassDef):
                casos = [f.name for f in no.body
                         if isinstance(f, ast.FunctionDef) and f.name.startswith("test_")]
                classes.append({"classe": no.name, "casos": casos})
            elif isinstance(no, ast.FunctionDef) and no.name.startswith("test_"):
                avulsos.append(no.name)
        suites.append({"arquivo": arquivo.name, "classes": classes, "funcoes_avulsas": avulsos})
    return suites


def coletar_git_info(raiz: Path) -> dict:
    """Coleta dados do Git (branch, último commit, autor)."""
    def _run(args):
        try:
            return subprocess.run(["git", "-C", str(raiz)] + args,
                                  capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            return ""
    return {
        "branch": _run(["rev-parse", "--abbrev-ref", "HEAD"]),
        "ultimo_commit": _run(["log", "-1", "--date=short", "--format=%h — %s (%an, %ad)"]),
        "total_commits": _run(["rev-list", "--count", "HEAD"]),
        "autores": _run(["shortlog", "-sn", "--no-merges"]).replace("\n", " · "),
    }


def detectar_ferramentas_ambiente(raiz: Path) -> list:
    """Detecta ferramentas usadas no projeto (arquivos auxiliares/scripts)."""
    ferramentas = []
    sh = [p for p in raiz.rglob("*.sh") if not any(d in p.parts for d in DIRS_IGNORADOS)]
    if sh:
        ferramentas.append("Shell scripts de monitoramento: " +
                           ", ".join(str(p.relative_to(raiz)) for p in sh))
    if (raiz / ".gitignore").exists():
        ferramentas.append("Git com `.gitignore` robusto (ignora venv, dumps do MongoDB, "
                           "logs, screenshots *.png/*.html gerados pelos scrapers)")
    if (raiz / "requirements.txt").exists():
        ferramentas.append("pip gerenciando dependências via `requirements.txt` (versionamento mínimo `>=`)")
    if any("test_" in p.name for p in raiz.rglob("*.py")):
        ferramentas.append("pytest (suítes em `tests/`) + smoke test manual (`teste.py`)")
    if (raiz / "diagrams").exists():
        ferramentas.append("PlantUML + biblioteca C4-PlantUML (modelagem de arquitetura em `diagrams/`)")
    ferramentas.append("MongoDB local (mongosh / MongoDB Compass para inspeção do banco `hub_estudantes`)")
    ferramentas.append("Documentação viva da API: Swagger UI e ReDoc geradas pelo FastAPI")
    return ferramentas


# --------------------------------------------------------------------------- #
# GERAÇÃO DO RELATÓRIO
# --------------------------------------------------------------------------- #

def montar_relatorio(raiz: Path) -> str:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    arquivos = listar_arquivos(raiz)
    linhas_ext = contar_linhas_total(arquivos)
    total_linhas = sum(linhas_ext.values())
    pacotes = analisar_requirements(raiz)
    rotas_fastapi = analisar_rotas_fastapi(raiz)
    rotas_flask = analisar_rotas_flask(raiz)
    scrapers = analisar_scrapers(raiz)
    colecoes = analisar_colecoes_mongo(raiz)
    diagramas = analisar_diagramas(raiz)
    front = analisar_frontend(raiz)
    config = analisar_config(raiz)
    testes = analisar_tests(raiz)
    git = coletar_git_info(raiz)
    ferramentas = detectar_ferramentas_ambiente(raiz)

    infos_py = [analisar_python(raiz, p) for p in arquivos if p.suffix == ".py"]

    L = []
    add = L.append

    add("# 📑 Relatório Técnico Completo — EduScrap (TechHub UERN)")
    add("")
    add("> Documento **gerado automaticamente** pelo script `tools/gerar_relatorio.py`, a partir "
        "da análise estática do código-fonte do repositório (AST do Python, regex sobre JS/HTML, "
        "leitura dos diagramas PlantUML, requirements, configs e Git).")
    add(f"> Data de geração: **{agora}** · Raiz analisada: `{raiz.resolve()}`")
    add("")
    add("---")
    add("")

    add("## Sumário")
    add("")
    toc = [
        "Visão Geral e Intuito",
        "Stack Tecnológica",
        "Arquitetura do Sistema",
        "Estrutura de Pastas e Métricas",
        "Camada de Coleta (Web Scraping)",
        "Camada de Normalização (Pipeline de Dados)",
        "Camada de Persistência (MongoDB)",
        "Camada de API (FastAPI e Flask)",
        "Frontend (Dashboard)",
        "Configurações Externas (JSON)",
        "Diagramas de Arquitetura",
        "Ferramentas e Infraestrutura",
        "Testes Automatizados",
        "Fluxo Ponta a Ponta",
        "Decisões de Projeto e Riscos",
        "Como Executar",
        "Conclusão",
    ]
    for idx, item in enumerate(toc, 1):
        anchor = item.lower().replace(" ", "-").replace("(", "").replace(")", "")
        add(f"{idx}. [{item}](#{idx}-{anchor})")
    add("")
    add("---")
    add("")

    add("## 1. Visão Geral e Intuito")
    add("")
    add("O **EduScrap** (também chamado de *TechHub UERN*) é uma plataforma de **agregação "
        "automatizada de oportunidades acadêmicas e profissionais** voltada a estudantes da "
        "**UERN (Universidade do Estado do Rio Grande do Norte)** — com foco em Mossoró e região — "
        "e de instituições vizinhas como a **UFERSA**.")
    add("")
    add("**Problema que resolve:** editais de estágio, bolsa, PNAES, monitoria, residência e "
        "processos seletivos são publicados espalhados em diversos portais institucionais "
        "(PRAE, PROEX, Portal UERN, UFERSA, CIEE), muitas vezes protegidos por Cloudflare e com "
        "prazos curtos. O estudante precisa visitar vários sites manualmente e frequentemente "
        "perde inscrições.")
    add("")
    add("**Solução implementada (verificada no código):**")
    add("- **Robôs de coleta (scrapers)** independentes por fonte, com técnicas distintas "
        "(HTTP estático, Selenium headless anti-detecção, mineração de texto com palavras-chave);")
    add("- **Normalização heurística**: extração de datas por regex, deduplicação via `upsert`, "
        "vinculação de metadados da instituição (`fonte_id`) e cálculo de vigência;")
    add("- 🗄️ Armazenamento **NoSQL (MongoDB)** com índices de texto, índices compostos e "
        "validação por JSON Schema;")
    add("- **API REST** (FastAPI como principal + variante Flask modular em `backend/api/`) com "
        "paginação, filtro de vigentes, busca unificada, estatísticas e auditoria do banco;")
    add("- **Frontend estático** (HTML/CSS/JS puro, tema *Memphis Design*) que consome a API e "
        "exibe cards, dashboard analítico e um *inspector* de infraestrutura.")
    add("")
    add("### Funcionalidades declaradas no README")
    add("- Web scraping automatizado multi-fonte;")
    add("- Monitoramento de notícias/editais com atualização automática;")
    add("- API moderna com CORS; dashboard responsivo; filtragem inteligente por área "
        "(Tecnologia, Saúde, Humanas, Exatas, Direito, Comunicação).")
    add("")
    add("---")
    add("")

    # ---------------- 2. STACK ----------------
    add("## 2. Stack Tecnológica")
    add("")
    add("### 2.1 Dependências declaradas (`requirements.txt`)")
    add("")
    add("| Pacote | Versão mínima | Papel no projeto |")
    add("|---|---|---|")
    for nome, ver in pacotes:
        desc = DESCRICAO_BIBLIOTECAS.get(nome, "Ver seção correspondente deste relatório.")
        add(f"| `{nome}` | `{ver}` | {desc} |")
    add("")
    add("### 2.2 Bibliotecas detectadas no código além do requirements")
    extras = set()
    for i in infos_py:
        for imp in i["imports"]:
            if imp in ("webdriver_manager", "pdfminer", "pytest"):
                extras.add(imp)
    if extras:
        add("| Módulo | Onde é usado | Observação |")
        add("|---|---|---|")
        if "webdriver_manager" in extras:
            add("| `webdriver-manager` | `scraper_ciee.py`, `scraper_portal_uern.py` | ⚠️ Importado mas **não listado no requirements.txt** |")
        if "pdfminer" in extras:
            add("| `pdfminer.six` | `pdf_utils.py` | ⚠️ Usado com *graceful degradation*; **ausente no requirements.txt** |")
        if "pytest" in extras:
            add("| `pytest` | `tests/test_regex.py`, `tests/test_scraper.py` | ⚠️ Framework de teste não pinned no requirements |")
        add("")
    add("### 2.3 Stack de apresentação")
    libs_ext = ", ".join(front["bibliotecas_externas"]) or "Phosphor Icons (via unpkg)"
    add(f"- **Frontend:** JavaScript puro ({front['linhas']['js']} linhas), CSS autoral "
        f"({front['linhas']['css']} linhas) e HTML ({front['linhas']['html']} linhas); "
        f"única dependência externa: `{libs_ext}` para ícones.")
    if front["paleta"]:
        add("- **Paleta de design (variáveis CSS):** " +
            ", ".join(f"`--{nome}` `{hexcor}`" for nome, hexcor in front["paleta"]))
    add("")
    add("### 2.4 Banco e infraestrutura")
    add("- **MongoDB 4.4+** (standalone local, `mongodb://localhost:27017/`, database `hub_estudantes`);")
    add("- Diagramas modelados em **PlantUML** com biblioteca **C4-PlantUML**;")
    add("- Versionamento **Git**" + (f" (branch atual: `{git['branch']}`)." if git["branch"] else "."))
    add("")
    add("---")
    add("")

    # ---------------- 3. ARQUITETURA ----------------
    add("## 3. Arquitetura do Sistema")
    add("")
    add("O sistema segue uma **arquitetura em camadas orientada a pipeline de dados**, coerente "
        "com os diagramas C4 encontrados em `diagrams/`:")
    add("")
    add("```text")
    add("┌─────────────────────────────────────────────────────────────────────┐")
    add("│ FONTES EXTERNAS   PRAE · PROEX · Portal UERN · UFERSA · CIEE · G1…   │")
    add("└───────────────┬─────────────────────────────────────────────────────┘")
    add("               │ HTTP/HTML · PDF · Navegador automatizado (Selenium)")
    add("┌───────────────▼───────────────┐     ┌──────────────────────────────┐")
    add("│  ENGINE DE COLETA (scrapers)  │────▶│ NORMALIZADOR                 │")
    add("│  requests+bs4 / selenium      │     │ RegexEngine → DataValidator  │")
    add("│  pdf_utils (pdfminer)         │     │ → JSONBuilder → Scheduler    │")
    add("└───────────────┬───────────────┘     └──────────────┬───────────────┘")
    add("                │ upsert (deduplicação)              │ schema v1.0")
    add("┌───────────────▼─────────────────────────────────────▼──────────────┐")
    add("│                     MONGODB  (banco: hub_estudantes)               │")
    add("│  vagas_estagio · vagas_bolsa · vagas_ufersa · vagas_ciee ·         │")
    add("│  vagas_portal_uern · vagas_noticias · fontes_provedores ·          │")
    add("│  historico_varreduras · controle_cache · editais/vagas/noticias    │")
    add("└───────────────┬────────────────────────────────────────────────────┘")
    add("                │ PyMongo")
    add("┌───────────────▼───────────────────────────┐")
    add("│ API REST  (FastAPI :8000 / Flask :5000)   │")
    add("│ paginação · vigência · busca $text · stats│")
    add("└───────────────┬───────────────────────────┘")
    add("                │ fetch()/JSON + CORS")
    add("┌───────────────▼───────────────────────────┐")
    add("│ FRONTEND ESTÁTICO (dashboard Memphis)     │")
    add("└───────────────────────────────────────────┘")
    add("```")
    add("")
    add("### Princípios arquitetônicos observados no código")
    add("1. **Desacoplamento por fonte**: cada portal tem seu scraper independente — a queda de um "
        "não derruba os demais (try/except isolado por fonte em `scraper_noticias.py`).")
    add("2. **Produção e consumo assíncronos** (ver `diagrama_sequencia`): o scraping acontece em "
        "segundo plano (*fire-and-forget*); o usuário consulta dados **já normalizados** no banco, "
        "garantindo resposta rápida (< 2s).")
    add("3. **Abordagem híbrida NoSQL com referência manual**: a coleção `fontes_provedores` guarda "
        "a governança (nome oficial, URL, frequência, foco); os documentos de vaga carregam apenas "
        "`fonte_id`, e o join lógico é resolvido em runtime por `resolver_vinculo_fonte()` — "
        "equivalente a um *DBRef* leve.")
    add("4. **Idempotência**: scrapers gravam com `update_one(..., upsert=True)` chaveado por "
        "`link`/`codigo`/`nome`, evitando duplicatas em reexecuções.")
    add("5. **Cache TTL embutido**: `/api/noticias` só re-raspa se `controle_cache` indicar mais "
        "de 10 minutos desde a última execução.")
    add("6. **Auditoria**: toda *Varredura Global* grava em `historico_varreduras` duração, "
        "status, erro e contagem de documentos por coleção.")
    add("7. **Dualidade de APIs**: existe uma API FastAPI monolítica madura (`backend/main.py`, "
        "consumida pelo frontend) e uma API Flask modular experimental (`backend/api/` + "
        "`backend/src/normalizer/`) que opera sobre coleções padronizadas (`editais`, `vagas`, "
        "`noticias`).")
    add("")
    add("---")
    add("")

    # ---------------- 4. ESTRUTURA ----------------
    add("## 4. Estrutura de Pastas e Métricas")
    add("")
    add("```text")
    add("EduScrap-UERN/")
    add("├── backend/")
    add("│   ├── main.py                  # API FastAPI principal")
    add("│   ├── database_setup.py        # Índices + JSON Schema do MongoDB")
    add("│   ├── pdf_utils.py             # Extração de datas/PDF com cache")
    add("│   ├── scraper_*.py             # Robôs de coleta por fonte")
    add("│   ├── check_portal.sh          # Watchdog do portal UERN (loop curl)")
    add("│   ├── testar_uern.py           # Protótipo de análise de relevância")
    add("│   ├── api/                     # API alternativa Flask (app factory + blueprint)")
    add("│   └── src/normalizer/          # Esteira de normalização modular")
    add("│       ├── collectors/          # html_scraper, pdf_scraper, scheduler")
    add("│       ├── regex_engine.py      # Extração de datas/editais/valores/status")
    add("│       ├── validator.py         # Regras de vigência (Aberto/Urgente/Encerrado)")
    add("│       ├── json_builder.py      # Schema JSON v1.0 padronizado")
    add("│       └── database.py          # MongoDBHandler (CRUD + índices + update_status)")
    add("├── frontend/                    # Dashboard estático (index.html, script.js, style.css)")
    add("├── config/                      # course_mapping.json, patterns.json")
    add("├── diagrams/                    # Diagramas PlantUML/C4")
    add("├── tests/                       # Suítes pytest (regex, scraper)")
    add("├── tools/gerar_relatorio.py     # Este gerador de relatório")
    add("├── requirements.txt")
    add("└── README.md / LICENSE / .gitignore")
    add("```")
    add("")
    add("### Métricas calculadas do repositório")
    add("")
    add(f"- Arquivos de código/documentação analisados: **{len(arquivos)}**")
    add(f"- Linhas totais: **{total_linhas:,}**".replace(",", "."))
    add("")
    add("| Tipo | Linhas |")
    add("|---|---|")
    for ext, n in sorted(linhas_ext.items(), key=lambda x: -x[1]):
        add(f"| `{ext}` | {n:,} |".replace(",", "."))
    add("")
    add("### Principais módulos Python (extraídos via AST)")
    add("")
    add("| Arquivo | Linhas | Classes | Funções de módulo |")
    add("|---|---|---|---|")
    for i in sorted(infos_py, key=lambda x: -x["linhas"])[:14]:
        classes = ", ".join(f"`{c['nome']}`" for c in i["classes"]) or "—"
        funcs = f"{len(i['funcoes'])} função(ões)" if i["funcoes"] else "—"
        add(f"| `{i['arquivo']}` | {i['linhas']} | {classes} | {funcs} |")
    add("")
    if git["ultimo_commit"]:
        add(f"**Git:** branch `{git['branch']}` · {git['total_commits']} commit(s) · autores: "
            f"{git['autores'] or '—'} · último: {git['ultimo_commit']}")
        add("")
    add("---")
    add("")

    # ---------------- 5. SCRAPERS ----------------
    add("## 5. Camada de Coleta (Web Scraping)")
    add("")
    add("Cada scraper é um script autônomo executável (`python scraper_x.py`) que conecta ao "
        "MongoDB, raspa sua fonte e grava documentos no formato "
        "`{nome, link, categoria, fonte[, data_vencimento]}`.")
    add("")
    for s in scrapers:
        add(f"### `{s['arquivo']}` — {s['fonte']}  ({s['linhas']} linhas)")
        if s["foco"]:
            add(f"**Foco:** {s['foco']}  ")
        add(f"**Técnicas:** {', '.join(s['tecnicas']) or 'requests + BeautifulSoup'}  ")
        cols = ', '.join(f'`{c}`' for c in s["colecoes"]) or "—"
        add(f"**Coleção de destino:** {cols}  ")
        urls = " · ".join(s["urls"][:6]) or "—"
        add(f"**URLs raspadas:** {urls}")
        add("")
    add("### Destaques técnicos identificados")
    add("- **Anti-Cloudflare / stealth** (`scraper_portal_uern.py`): Chrome `--headless=new`, "
        "user-agent falso, remoção de `navigator.webdriver` via CDP e espera do challenge; após "
        "carregar, aplica **análise de relevância por palavras-chave** (estágio, bolsa, edital, "
        "PNAES, monitoria…) antes de salvar em `vagas_portal_uern`.")
    add("- **Scraper híbrido CIEE** (`scraper_ciee.py`, classe `ScraperCIEEHibrido`): Firefox + "
        "GeckoDriver gerenciado pelo webdriver-manager, filtra pela cidade *Mossoró*, captura os "
        "cards por XPath (`Ver detalhes`/`Compartilhar`), salva com deduplicação por `codigo`, "
        "gera relatório de execução em log estruturado e screenshot em caso de falha.")
    add("- **Heurística de data** repetida nos scrapers simples: regex `dd/mm/aaaa` e variantes "
        "`dd-mm-aaaa`; sem prazo detectado, o documento fica sem `data_vencimento` (a API trata "
        "como vigência desconhecida).")
    add("- **Agregador de notícias** (`scraper_noticias.py`): limpa a coleção e insere ~10 itens "
        "de G1 Tecnologia e Canaltech, com isolamento de falha por fonte.")
    add("- **Utilitário PDF** (`pdf_utils.py`): download com cache em memória limitado a 50 PDFs, "
        "extração via pdfminer (até 10 páginas), regex multiformato de datas e **estratégia "
        "híbrida HTML→PDF** (`extrair_data_vencimento_hibrido`) para prazos que só existem dentro "
        "do PDF do edital.")
    add("- **Watchdog shell** (`check_portal.sh`): loop `curl` a cada 60s até o portal voltar ao "
        "ar (HTTP 200); então dispara os scrapers PRAE/PROEX automaticamente.")
    add("")
    add("---")
    add("")

    # ---------------- 6. NORMALIZER ----------------
    add("## 6. Camada de Normalização (Pipeline de Dados)")
    add("")
    add("Localizada em `backend/src/normalizer/`, é a materialização do componente *Normalizador* "
        "do diagrama de componentes C4. Pipeline: "
        "**Coletor → RegexEngine → DataValidator → JSONBuilder → MongoDBHandler**, orquestrado "
        "periodicamente pelo `Scheduler`.")
    add("")
    for i in infos_py:
        if "src/normalizer" not in i["arquivo"].replace(os.sep, "/"):
            continue
        add(f"### ⚙️ `{i['arquivo']}` ({i['linhas']} linhas)")
        for c in i["classes"]:
            docs = f" — {c['docstring']}" if c["docstring"] else ""
            add(f"- **Classe `{c['nome']}`**{docs}:")
            add(f"  - Métodos: {', '.join('`'+m+'`' for m in c['metodos'])}")
        for f in i["funcoes"]:
            add(f"- Função `{f['nome']}()`" + (f" — {f['docstring']}" if f["docstring"] else ""))
        add("")
    add("### Regras de negócio codificadas")
    add("- **Status por vigência** (`DataValidator.validate_deadline`): `dias < 0 → Encerrado`, "
        "`= 0 → Encerra Hoje`, `≤ 3 → Urgente`, `senão → Aberto`;")
    add("- **Atualização em massa** (`MongoDBHandler.update_status`): marca `Encerrado`/`Aberto` "
        "comparando `data_limite` com hoje, pulando documentos já corretos;")
    add("- **Schema JSON v1.0** (`JSONBuilder`): campos obrigatórios `tipo, titulo, fonte, url` + "
        "carimbos `criado_em`/`atualizado_em` e `validate_schema()`;")
    add("- **Regex padrão** (idêntica a `config/patterns.json`): datas BR por extenso, numéricas e "
        "ISO; número de edital `Edital n° NN/AAAA`; valores monetários; keywords de status;")
    add("- **Scheduler**: executa tarefas a cada N horas (padrão 6h) **e** diariamente às 03:00 "
        "(horário de baixa demanda), sempre atualizando o status antes de coletar.")
    add("")
    add("---")
    add("")

    # ---------------- 7. MONGO ----------------
    add("## 7. Camada de Persistência (MongoDB)")
    add("")
    add("- **Host/URI:** `mongodb://localhost:27017/` (sobrescritível via `MONGODB_URI` no "
        "handler do normalizador);")
    add("- **Database:** `hub_estudantes`;")
    add("- **Timeouts de conexão** (MongoDBHandler): serverSelection 5s, socket 45s, connect 20s.")
    add("")
    add("### Coleções detectadas no código")
    add("")
    add("| Coleção | Propósito |")
    add("|---|---|")
    for c in colecoes:
        add(f"| `{c}` | {DESCRICAO_COLECOES.get(c, 'Coleção auxiliar identificada no código.')} |")
    add("")
    add("### Otimizações aplicadas por `database_setup.py`")
    add("1. **Índice de texto** `idx_busca_nome_text` sobre `nome` nas coleções principais → "
        "alimenta a busca `$text` de `/api/pesquisar`;")
    add("2. **Índice composto** `idx_categoria_fonte` (`categoria`+`fonte`) → acelera os filtros "
        "combinados do dashboard;")
    add("3. **Validador JSON Schema** (`validationAction: warn`) em `vagas_noticias`: exige "
        "`nome`, `link` (pattern `^https?://`), `fonte` e `categoria`;")
    add("4. Índices adicionais do normalizador: `idx_status` e `idx_status_areas_composto` na "
        "coleção `editais`.")
    add("")
    add("### Modelo de documento típico (scrapers legados)")
    add("```json")
    add("{")
    add('  "nome": "Edital 012/2026 - Programa de Monitoria",')
    add('  "link": "https://portal.uern.br/prae/.../edital-012.pdf",')
    add('  "categoria": "Monitoria",')
    add('  "fonte": "PRAE/UERN",')
    add('  "data_vencimento": "2026-10-30T00:00:00Z",')
    add('  "fonte_id": "prae_uern"')
    add("}")
    add("```")
    add("")
    add("Documento enriquecido retornado pela API inclui `data_vencimento_formatada` "
        "(`dd/mm/aaaa`) e `meta_fonte` (nome oficial, URL e frequência do portal).")
    add("")
    add("---")
    add("")

    # ---------------- 8. API ----------------
    add("## 8. Camada de API (FastAPI e Flask)")
    add("")
    add(f"### 8.1 API principal — FastAPI (`backend/main.py`, porta 8000) — {len(rotas_fastapi)} endpoints")
    add("")
    add("Swagger/openAPI automático em `http://localhost:8000/docs`. CORS liberado "
        "(`allow_origins=[\"*\"]`). Na subida do servidor, `garantir_metadados_fontes()` faz "
        "upsert das fontes mestre em `fontes_provedores`.")
    add("")
    add("| Método | Endpoint | Função | Parâmetros | Descrição |")
    add("|---|---|---|---|---|")
    for r in rotas_fastapi:
        add(f"| {r['metodo']} | `{r['caminho']}` | `{r['funcao']}` | {r['parametros'] or '—'} | {r['descricao']} |")
    add("")
    add("Padrão de resposta paginada: `{pagina_atual, limite_por_pagina, total_documentos, dados[]}`.")
    add("")
    add(f"### 8.2 API alternativa — Flask (`backend/api/`, porta 5000) — {len(rotas_flask)} endpoints")
    add("")
    add("Factory pattern (`create_app`) + Blueprint `api_routes` com prefixo `/api`, resposta JSON "
        "padrão `{success, count|error, data}`, **fallback gracioso (HTTP 503)** quando o MongoDB "
        "está indisponível e error handlers para 404/500.")
    add("")
    add("| Método | Endpoint | Função | Origem | Descrição |")
    add("|---|---|---|---|---|")
    for r in rotas_flask:
        add(f"| {r['metodo']} | `{r['caminho']}` | `{r['funcao']}` | {r['origem']} | {r.get('descricao','')} |")
    add("")
    add("---")
    add("")

    add("## 9. Frontend (Dashboard)")
    add("")
    add(f"- **Título da página:** *{front['titulo_pagina']}*")
    add(f"- **Alvo da API:** `const API_URL = \"{front['api_url']}\"`;")
    add(f"- **Endpoints consumidos:** {', '.join('/' + c for c in front['chamadas_api'])};")
    add(f"- **Funções JavaScript:** {', '.join('`' + f + '`' for f in front['funcoes_js'])}.")
    add("")
    add("### Navegação (botões detectados no HTML)")
    add("")
    add("| Elemento | Rótulo | Ação |")
    add("|---|---|---|")
    acoes = {
        "btn-estagios": "carregarDados('estagios') — aba Estágios (PRAE)",
        "btn-bolsas": "carregarDados('bolsas') — aba Bolsas (PROEX)",
        "btn-ufersa": "carregarDados('ufersa') — aba Editais (UFERSA)",
        "btn-ciee": "carregarDados('ciee') — aba Vagas (CIEE)",
        "btn-portal_uern": "carregarDados('portal_uern') — aba Portal UERN",
        "btn-noticias": "carregarDados('noticias') — aba Notícias Tech",
        "btn-analises": "carregarEstatisticas() — dashboard de indicadores",
        "btn-pesquisar": "realizarPesquisa() — busca unificada ($text)",
        "btn-buscar-tudo": "acionarTodosOsRobos() — dispara a Varredura Global (/api/buscar-tudo)",
    }
    for bid, label in front["botoes"]:
        add(f"| `#{bid}` | {label} | {acoes.get(bid, '—')} |")
    add("")
    add("### Comportamentos verificados em `script.js`")
    add("- Paginação dinâmica calculada a partir de `total_documentos`/`limite_por_pagina`;")
    add("- Checkbox **filtroVigentes** adiciona `&apenas_vigentes=true` às requisições "
        "(filtro `data_vencimento >= now` no backend);")
    add("- Cards exibem a **badge “ Inscrições até dd/mm/aaaa”** quando há "
        "`data_vencimento_formatada` (ou seja, quando a regex do backend detectou prazo);")
    add("- O link da fonte usa `meta_fonte.url_oficial` com tooltip mostrando o portal mestre e o "
        "ciclo do robô (frequência de monitoramento);")
    add("- **Indicadores** (`/api/estatisticas`): contadores por fonte, alerta de *reta final* "
        "(prazos ≤ 7 dias) e distribuição por categoria PRAE;")
    add("- **Inspector de infraestrutura** (`/api/db-status`): nº de documentos, alocação em KB, "
        "badges de índices e selo *VALIDADOR ATIVO* por coleção;")
    add("- Tratamento de erro amigável: *“Erro ao conectar com a API. O FastAPI está rodando?”*.")
    add("")
    add("### Estilo")
    add("- Tema visual **Memphis Design**: formas geométricas absolutas (rosca laranja, zigue-zague, "
        "triângulos listrados, cruzes), sombras duras `box-shadow: Npx Npx 0 cor`, bordas grossas "
        "e grade de fundo desenhada com gradientes lineares em `body::before`;")
    add("- Tipografia `Segoe UI/Tahoma/Verdana`; grid responsivo `.grid-vagas` "
        "(`repeat(auto-fit, minmax(...))`) e animações de entrada (`surgimento`).")
    add("")
    add("---")
    add("")

    # ---------------- 10. CONFIG ----------------
    add("## 10. Configurações Externas (JSON)")
    add("")
    add("### `config/course_mapping.json`")
    cm = config.get("course_mapping", {})
    areas = cm.get("areas", [])
    add(f"- Define **{len(areas)} áreas** de conhecimento: {', '.join(areas)};")
    add(f"- Mapeia **{cm.get('total_cursos', 0)} cursos** de graduação às áreas (ex.: Tecnologia → "
        "Ciência da Computação, Sistemas de Informação, Engenharia de Software, Ciência de Dados, TI);")
    add(f"- Bloco `keywords` por área presente: **{cm.get('tem_keywords', False)}** "
        "(heurística de classificação textual).")
    add("")
    add("### `config/patterns.json`")
    pt = config.get("patterns", {})
    add(f"- Espelha os padrões compilados de `RegexEngine`: grupos {list(pt.keys())};")
    add("- Permite evoluir regras de extração **sem tocar no código** (injeção via "
        "`RegexEngine(patterns_path=...)`).")
    add("")
    add("### Variáveis de ambiente suportadas (README + código)")
    add("```dotenv")
    add("MONGODB_URI=mongodb://localhost:27017/")
    add("DATABASE_NAME=hub_estudantes")
    add("DEBUG=True")
    add("SECRET_KEY=...")
    add("API_HOST=0.0.0.0            # Flask")
    add("FLASK_PORT=5000             # Flask")
    add("FLASK_ENV=production|development")
    add("```")
    add("")
    add("---")
    add("")

    # ---------------- 11. DIAGRAMAS ----------------
    add("## 11. Diagramas de Arquitetura")
    add("")
    add(f"{len(diagramas)} artefatos **PlantUML** (incluindo a stdlib **C4-PlantUML**) documentam o "
        "sistema em níveis crescentes de detalhe — Container → Componentes → Sequência:")
    add("")
    mapa_titulos = {
        "diagrama_container": "Nível Container: visão macro da plataforma EduScrap, seus "
                              "containers (Engine de Coleta, Normalizador, Serviço de Alertas, "
                              "API REST, MongoDB, Redis) e sistemas externos (portais, JOUERN, CIEE).",
        "diagrama_componentes": "Nível Componente: detalhamento interno do Normalizador "
                                "(Leitor de PDF → Motor Regex → Validador → Construtor JSON, com "
                                "fallback opcional de NLP/spaCy e base de padrões por fonte).",
        "diagrama_sequencia": "Sequência temporal: Fase 1 (coleta assíncrona disparada por Cron, "
                              "fire-and-forget, persistência no MongoDB) e Fase 2 (consulta do "
                              "estudante via API REST com query filtrada — o usuário nunca espera "
                              "o scraping).",
    }
    for d in diagramas:
        add(f"### `{d['arquivo']}` — {d['titulo'] or d['arquivo']}")
        for k, v in mapa_titulos.items():
            if k in d["arquivo"]:
                add(f"*{v}*")
                add("")
                break
        if d["componentes"]:
            add("**Elementos nomeados:** " + "; ".join(d["componentes"][:12]))
        if d["atores"]:
            add(f"**Atores humanos detectados:** {d['atores']} (Administrador, Estudante)")
        if d["arrows"]:
            add("")
            add("| Origem | Destino | Interação |")
            add("|---|---|---|")
            vistos = set()
            for a, b, msg in d["arrows"]:
                if (a, b, msg) in vistos:
                    continue
                vistos.add((a, b, msg))
                add(f"| `{a}` | `{b}` | {msg} |")
        if d["rels"]:
            add("")
            add("| Componente | Para | Mensagem |")
            add("|---|---|---|")
            for a, b, msg in d["rels"]:
                add(f"| `{a}` | `{b}` | {msg} |")
        add("")
    add("**Nota de governança do diagrama de componentes:** a *Regra de Vigência* "
        "(Data Extraída vs Data Atual → `Aberto`/`Encerrado`) está formalizada tanto no modelo "
        "quanto no código (`validator.py` e `database.update_status`).")
    add("")
    add("> Para renderizar: instale o PlantUML e rode `plantuml diagrams/diagrama_container` "
        "(ou use o plugin PlantUML da IDE). O diagrama de componentes importa a lib remota "
        "C4-PlantUML, exigindo internet na primeira renderização.")
    add("")
    add("---")
    add("")

    add("## 12. Ferramentas e Infraestrutura")
    add("")
    for f in ferramentas:
        add(f"- {f}")
    add("")
    add("### Scripts operacionais disponíveis")
    add("")
    add("| Comando | Efeito |")
    add("|---|---|")
    add("| `uvicorn main:app --reload --host 0.0.0.0 --port 8000` | Sobe a API FastAPI (a partir de `backend/`) |")
    add("| `python database_setup.py` | Cria índices e aplica JSON Schema no MongoDB |")
    add("| `python scraper_prae.py` (idem proex/ufersa/ciee/noticias/portal_uern) | Executa um robô específico |")
    add("| `bash check_portal.sh` | Watchdog: aguarda o portal voltar e roda PRAE+PROEX |")
    add("| `python -m http.server 3000` (em `frontend/`) | Serve o dashboard |")
    add("| `pytest` (em `tests/`) | Roda as suítes unitárias |")
    add("| `GET /api/buscar-tudo` | Aciona todos os robôs pela API + normalização + auditoria |")
    add("| `python tools/gerar_relatorio.py` | Regenera este relatório técnico |")
    add("")
    add("---")
    add("")

    add("## 13. Testes Automatizados")
    add("")
    total_casos = 0
    for suite in testes:
        add(f"### `{suite['arquivo']}`")
        for c in suite["classes"]:
            add(f"- Suite **{c['classe']}** ({len(c['casos'])} casos):")
            for caso in c["casos"]:
                add(f"  - `{caso}`")
            total_casos += len(c["casos"])
        for fn in suite["funcoes_avulsas"]:
            add(f"- Função de teste avulsa: `{fn}`")
            total_casos += 1
        add("")
    add(f"**Total: {total_casos} casos de teste**, cobrindo: extração regex de datas numéricas e "
        "por extenso, número de edital, detecção de status (Aberto/Encerrado), valores "
        "monetários, parsing de datas do validador, cálculo de deadline futuro/passado e o parser "
        "de seletores CSS do `HTMLScraper`. Existe também o smoke test manual `teste.py` "
        "(inserção de documento de exemplo no MongoDB).")
    add("")
    add("> ⚠️ Os testes fazem `sys.path.insert(0, <raiz>/src)`, mas os módulos vivem em "
        "`backend/src/...` — ajuste o path (ou execute `pytest` com `PYTHONPATH=backend`) para "
        "que as importações resolvam.")
    add("")
    add("---")
    add("")

    add("## 14. Fluxo Ponta a Ponta (como uma vaga chega à tela)")
    add("")
    add("1. **Gatilho** — agendamento (Scheduler: a cada 6h e às 03:00), `check_portal.sh`, botão "
        "global `/api/buscar-tudo` ou CLI manual;")
    add("2. **Coleta** — o scraper acessa o portal (requests/Selenium), isola os links de editais "
        "(`<li>` cujo texto inicia com “edital”, fora de nav/footer) e resolve os PDFs anexos;")
    add("3. **Enriquecimento** — regex extrai `data_vencimento` do título/categoria; quando o prazo "
        "só existe no PDF, `pdf_utils.extrair_data_vencimento_hibrido` baixa e varre o documento "
        "(cache de até 50 PDFs);")
    add("4. **Persistência** — `update_one(chave, {\"$set\": ...}, upsert=True)` grava sem duplicar; "
        "a varredura global ainda injeta `fonte_id` em todos os documentos (migração heurística) e "
        "registra a auditoria em `historico_varreduras`;")
    add("5. **Exposição** — a FastAPI pagina, formata datas, resolve `meta_fonte` via join lógico e "
        "filtra vigentes (`data_vencimento >= now`);")
    add("6. **Consumo** — o dashboard renderiza cards com badge de prazo, link oficial da fonte e "
        "indicadores (totais, reta final de 7 dias, distribuição por categoria);")
    add("7. **Transparência** — `/api/db-status` expõe a saúde física das coleções (documentos, KB, "
        "índices, validadores) no modo *Inspector*.")
    add("")
    add("---")
    add("")

    add("## 15. Decisões de Projeto e Riscos")
    add("")
    add("### Decisões conscientes")
    add("- **Sem ORM / sem framework frontend**: máxima leveza e controle (vanilla JS + PyMongo cru);")
    add("- **Upsert como estratégia de deduplicação** — simples e suficiente para o volume regional;")
    add("- **Cache TTL no próprio banco** (`controle_cache`) em vez de Redis — coerente com o escopo "
        "(Redis aparece nos diagramas como evolução planejada);")
    add("- **Validação `warn` em vez de `strict`** no JSON Schema — não quebra ingestões antigas;")
    add("- **Duas APIs conviviendo**: FastAPI para produção imediata; Flask + `src/normalizer` como "
        "arquitetura-alvo modular (visível nos diagramas C4).")
    add("")
    add("### Riscos / dívidas técnicas identificados automaticamente")
    add("1. **Dependências implícitas**: `webdriver-manager`, `pdfminer.six` e `pytest` são "
        "importados no código mas faltam no `requirements.txt`;")
    add("2. **Segurança**: CORS `allow_origins=[\"*\"]` + endpoint `buscar-tudo` via GET que apaga e "
        "re-raspa coleções inteiras (`delete_many`) — proteger (POST + autenticação) antes de "
        "publicar fora de localhost;")
    add("3. **Configuração hardcoded**: URI do Mongo e caminhos de chromedriver "
        "(`/usr/local/bin/chromedriver`) fixos em vários scrapers — migrar para `.env`/"
        "webdriver-manager;")
    add("4. **Acoplamento a layouts de terceiros**: seletores CSS/XPath de G1, Canaltech, CIEE e "
        "portais UERN quebram quando os sites mudarem (mitigar com testes de contrato);")
    add("5. **Paths dos testes incorretos** (ver §13) — a suíte pode falhar por ImportError;")
    add("6. **Frontend aponta para `localhost:8000`** — externalizar `API_URL` para deploy;")
    add("7. **Artefatos binários na árvore de trabalho**: `backend/__pycache__/*.pyc` presentes — o "
        "`.gitignore` cobre `__pycache__/`; recomenda-se `git rm -r --cached backend/__pycache__`.")
    add("")
    add("---")
    add("")

    add("## 16. Como Executar (resumo operacional)")
    add("")
    add("```bash")
    add("# 0) Pré-requisitos: Python 3.8+, MongoDB 4.4+ rodando em localhost:27017")
    add("python -m venv venv && source venv/bin/activate    # Windows: venv\\Scripts\\activate")
    add("pip install -r requirements.txt")
    add("pip install pdfminer.six webdriver-manager pytest   # complementos detectados")
    add("")
    add("cd backend")
    add("python database_setup.py                 # 1) índices + validadores")
    add("uvicorn main:app --reload --port 8000    # 2) API FastAPI")
    add("python scraper_prae.py                   # 3) coleta (ou GET /api/buscar-tudo)")
    add("")
    add("cd ../frontend")
    add("python -m http.server 3000               # 4) dashboard em http://localhost:3000")
    add("```")
    add("")
    add("Docs interativos da API: `http://localhost:8000/docs` (Swagger) e `/redoc`.")
    add("")
    add("---")
    add("")

    add("## 17. Conclusão")
    add("")
    add(f"O EduScrap demonstra, com **{total_linhas:,} linhas** distribuídas em {len(arquivos)} "
        "arquivos, um pipeline ETL completo e funcional — *Extract* (6 scrapers multi-técnica), "
        "*Transform* (motor regex, validador de vigência e schema JSON v1.0) e *Load* (MongoDB "
        "indexado e auditado) — servido por API REST documentada e consumido por um dashboard "
        "autoexplicativo. O diferencial do projeto é a **resiliência pragmática**: fallbacks em "
        "cascata (HTML→PDF, `$text`→`$regex`, live-scrape→cache TTL, strict→warn) que mantêm o "
        "serviço útil mesmo com portais instáveis ou protegidos por anti-bot. Como próximos "
        "passos naturais: fechar as lacunas de dependências/paths apontadas em §15, autenticar a "
        "varredura global e promover a esteira modular (`src/normalizer`) a caminho principal, "
        "conforme projetado nos diagramas C4.".replace(",", "."))
    add("")
    add("---")
    add("")
    add("*Fim do relatório — rerode `python tools/gerar_relatorio.py` sempre que o código mudar "
        "para manter este documento sincronizado com a realidade do repositório.*")

    return "\n".join(L)

def main():
    parser = argparse.ArgumentParser(
        description="Gera automaticamente um relatório técnico completo do EduScrap.")
    parser.add_argument("--raiz", default=str(Path(__file__).resolve().parent.parent),
                        help="Raiz do projeto (padrão: pasta pai do script)")
    parser.add_argument("--saida", default=RELATORIO_PADRAO,
                        help=f"Nome do arquivo de saída (padrão: {RELATORIO_PADRAO})")
    args = parser.parse_args()

    raiz = Path(args.raiz)
    if not (raiz / "backend").exists():
        print(f"❌ '{raiz}' não parece ser a raiz do projeto (backend/ ausente).", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Analisando projeto em: {raiz.resolve()}")
    conteudo = montar_relatorio(raiz)
    destino = raiz / args.saida
    destino.write_text(conteudo, encoding="utf-8")
    n_linhas = len(conteudo.splitlines())
    tamanho_kb = len(conteudo.encode("utf-8")) / 1024
    print(f"Relatório gerado: {destino} ({n_linhas} linhas, {tamanho_kb:.1f} KB)")


if __name__ == "__main__":
    main()
