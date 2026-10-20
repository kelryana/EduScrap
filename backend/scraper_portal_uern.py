##backend/scraper_portal_uern.py
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import logging
import os
import sys
from pathlib import Path
import requests
import urllib3

urllib3.disable_warnings()

from dotenv import load_dotenv
from pymongo import MongoClient

# Garante diretório backend no sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from pdf_utils import extrair_data_de_texto
from base_scraper import configurar_log_scraper
from src.normalizer.classifier import classificar_oportunidade

# Carrega variáveis de ambiente do .env na raiz do projeto
load_dotenv(BACKEND_DIR.parent / ".env")

logger = logging.getLogger("scraper_portal_uern")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

HEADERS_PADRAO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def conectar_banco():
    """Conecta ao MongoDB e retorna a coleção vagas_portal_uern"""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["vagas_portal_uern"]


# Palavras-chave para filtrar oportunidades relevantes
PALAVRAS_CHAVE_OPORTUNIDADES = [
    "estágio", "estágios", "bolsa", "bolsas", "vaga", "vagas",
    "seleção", "edital", "pnaes", "auxílio", "residência", "monitoria",
    "inscrições", "cursos", "vagas abertas", "processo seletivo",
    "extensão", "pesquisa", "iniciação científica", "notícia", "publicação",
    "chamada", "convocação", "aviso", "comunicado", "evento", "atividade"
]


def criar_navegador_headless():
    from driver_factory import obter_driver
    preferencia = os.getenv("SELENIUM_BROWSER", "auto")
    logger.info(f"Inicializando navegador para Portal UERN (preferência: {preferencia})...")
    return obter_driver(
        preferencia=preferencia,
        headless=True,
        timeout_pagina=25,
        timeout_implicito=2,
        fallback=True
    )


def extrair_data_do_texto(texto):
    if not texto:
        return None

    padroes = [
        r"\b(\d{2})/(\d{2})/(\d{4})\b",  # DD/MM/YYYY
        r"\b(\d{2})-(\d{2})-(\d{4})\b",  # DD-MM-YYYY
        r"\b(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})\b"  # DD de Mês de YYYY
    ]

    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 3:
                    g1, g2, g3 = match.groups()
                    if "Mês" in padrao:
                        meses = {
                            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
                            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
                            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
                        }
                        mes_num = meses.get(g2.lower(), 1)
                        return datetime(int(g3), mes_num, int(g1))
                    else:
                        return datetime(int(g3), int(g2), int(g1))
            except (ValueError, AttributeError):
                pass

    return None


def analisar_relevancia(texto):
    if not texto:
        return False, []

    texto_lower = texto.lower()
    palavras_encontradas = []

    for palavra in PALAVRAS_CHAVE_OPORTUNIDADES:
        if palavra in texto_lower:
            palavras_encontradas.append(palavra)

    return len(palavras_encontradas) > 0, palavras_encontradas


def _construir_resultado_oportunidade(url_noticia: str, titulo: str, resumo: str, texto_completo: str) -> dict:
    conteudo_analise = f"{titulo} {resumo} {texto_completo[:500]}"
    eh_relevante, palavras_chave = analisar_relevancia(conteudo_analise)

    if not eh_relevante:
        return {"relevante": False, "titulo": titulo, "url": url_noticia}

    data_str = extrair_data_de_texto(f"{titulo} {texto_completo}")
    data_vencimento = datetime.strptime(data_str, "%Y-%m-%d") if data_str else None

    categoria = "Notícia Geral"
    if any(p in palavras_chave for p in ["estágio", "vaga", "seleção", "processo seletivo"]):
        categoria = "Seleção de Estágio"
    elif any(p in palavras_chave for p in ["bolsa", "bolsas", "extensão", "pesquisa", "edital"]):
        categoria = "Bolsas e Editais"
    elif any(p in palavras_chave for p in ["curso", "cursos", "inscrições"]):
        categoria = "Cursos e Inscrições"

    texto_resumo = resumo[:250] if resumo else texto_completo[:250]
    classificacao = classificar_oportunidade(titulo, f"{texto_resumo} {' '.join(palavras_chave)}")
    cursos = classificacao.get("cursos") or []
    areas = classificacao.get("areas") or ["Geral / Universitário"]

    documento = {
        "nome": titulo,
        "titulo": titulo,
        "descricao": texto_resumo or titulo,
        "resumo": (resumo[:200] if resumo else texto_completo[:200]) or titulo,
        "link": url_noticia,
        "url": url_noticia,
        "categoria": categoria,
        "fonte": "Portal UERN",
        "fonte_id": "portal_uern_oficial",
        "status": "Aberto",
        "palavras_chave": palavras_chave,
        "cursos": cursos,
        "areas": areas,
        "geral": classificacao.get("geral", True),
        "data_mineracao": datetime.now(),
        "coletado_em": datetime.now().isoformat(),
    }

    if data_vencimento:
        documento["data_vencimento"] = data_vencimento

    return {
        "relevante": True,
        "titulo": titulo,
        "url": url_noticia,
        "palavras_chave": palavras_chave,
        "data_vencimento": data_vencimento,
        "documento": documento,
    }


def _analisar_html_noticia(url_noticia: str, html_interna: str) -> dict:
    soup_interna = BeautifulSoup(html_interna, "html.parser")

    titulo_tag = soup_interna.find("h1")
    titulo = titulo_tag.get_text(strip=True) if titulo_tag else "Título não identificado"

    corpo = (
        soup_interna.find(
            class_=re.compile(r"entry-content|post-content|single-content|td-post-content")
        )
        or soup_interna.find("article")
        or soup_interna
    )
    paragrafos = corpo.find_all("p")
    texto_completo = " ".join([p.get_text(strip=True) for p in paragrafos])

    meta_desc = soup_interna.find("meta", attrs={"name": "description"})
    resumo = meta_desc.get("content", "") if meta_desc else ""

    return _construir_resultado_oportunidade(url_noticia, titulo, resumo, texto_completo)


def _extrair_links_listagem(html_source: str) -> list:
    soup = BeautifulSoup(html_source, "html.parser")
    conteudo_principal = (
        soup.find("main")
        or soup.find(id="content")
        or soup.find(id="primary")
        or soup
    )
    links_ancora = conteudo_principal.find_all("a", href=True)

    urls_noticias = []
    for ancora in links_ancora:
        url = ancora.get("href", "")
        if "portal.uern.br/blog/" in url and "/blog/" in url:
            url_limpa = url.split("?")[0].rstrip("/")
            if any(
                ignorar in url_limpa
                for ignorar in ["/category/", "/categoria/", "/tag/", "/author/", "/page/"]
            ):
                continue
            if url_limpa not in urls_noticias:
                urls_noticias.append(url_limpa)
    return urls_noticias


def minerar_portal_uern():
    configurar_log_scraper(
        "portal_uern",
        "Portal UERN (Mineração Textual)",
        "vagas_portal_uern"
    )
    logger.info("=" * 70)
    logger.info("INICIANDO MINERAÇÃO DO PORTAL UERN (HÍBRIDO API/HTTP + SELENIUM)")
    logger.info("=" * 70)

    colecao = conectar_banco()
    driver = None
    session = requests.Session()
    url_principal = "https://portal.uern.br/todas-as-noticias/"
    url_wp_api = "https://portal.uern.br/wp-json/wp/v2/posts?per_page=15"

    noticias_validas = []
    links_ativos = []

    try:
        logger.info(f"Passo 1: Consultando publicações recentes do Portal UERN...")
        artigos_pre_carregados = []

        # Camada 1: API oficial WordPress do Portal UERN (retorna título, resumo e texto completo das 15 matérias em 1 requisição)
        try:
            resp_api = session.get(url_wp_api, headers=HEADERS_PADRAO, timeout=20)
            if resp_api.status_code == 200:
                posts_json = resp_api.json()
                if isinstance(posts_json, list) and len(posts_json) > 0:
                    for post in posts_json:
                        link_post = (post.get("link") or "").split("?")[0].rstrip("/")
                        titulo_html = (post.get("title") or {}).get("rendered") or ""
                        resumo_html = (post.get("excerpt") or {}).get("rendered") or ""
                        corpo_html = (post.get("content") or {}).get("rendered") or ""

                        titulo_limpo = BeautifulSoup(titulo_html, "html.parser").get_text(" ", strip=True)
                        resumo_limpo = BeautifulSoup(resumo_html, "html.parser").get_text(" ", strip=True)
                        corpo_limpo = BeautifulSoup(corpo_html, "html.parser").get_text(" ", strip=True)

                        if link_post and titulo_limpo:
                            artigos_pre_carregados.append({
                                "url": link_post,
                                "titulo": titulo_limpo,
                                "resumo": resumo_limpo,
                                "texto": corpo_limpo,
                            })
                    logger.info(f"✅ {len(artigos_pre_carregados)} notícias completas carregadas em lote do Portal UERN!")
        except Exception as e_api:
            logger.warning(f"Aviso na consulta direta à API WP ({e_api}), usando listagem HTML...")

        # Camada 2 (se API WP não retornou): HTML direto ou Selenium Anti-Cloudflare
        urls_noticias = []
        if not artigos_pre_carregados:
            try:
                resp = session.get(url_principal, headers=HEADERS_PADRAO, timeout=20)
                if resp.status_code == 200:
                    urls_noticias = _extrair_links_listagem(resp.text)[:12]
            except Exception as e_http:
                logger.warning(f"Aviso no acesso HTTP direto ({e_http}), acionando Selenium...")

            if not urls_noticias:
                logger.info("Passo 1.b: Inicializando navegador Selenium com stealth...")
                driver = criar_navegador_headless()
                driver.get(url_principal)
                time.sleep(5)
                urls_noticias = _extrair_links_listagem(driver.page_source)[:12]

        total_analisar = len(artigos_pre_carregados) or len(urls_noticias)
        logger.info(f"Passo 2: Selecionadas {total_analisar} notícias recentes para análise profunda (Text Mining)")

        if artigos_pre_carregados:
            for i, art in enumerate(artigos_pre_carregados, start=1):
                url_noticia = art["url"]
                logger.info(f"[{i}/{total_analisar}] Analisando: {url_noticia[:65]}...")
                resultado = _construir_resultado_oportunidade(
                    url_noticia, art["titulo"], art["resumo"], art["texto"]
                )
                if resultado["relevante"]:
                    doc = resultado["documento"]
                    dt_venc = resultado["data_vencimento"]
                    kws = resultado["palavras_chave"]

                    logger.info(f"   ✅ OPORTUNIDADE DETECTADA: {doc['titulo'][:75]}")
                    logger.info(f"   Palavras-chave: {', '.join(kws[:5])} | Categoria: {doc['categoria']}")
                    if dt_venc:
                        logger.info(f"   Prazo de inscrição detectado: {dt_venc.strftime('%d/%m/%Y')}")
                    else:
                        logger.info("   ℹ️ Oportunidade sem prazo específico detectado")

                    colecao.update_one({"link": url_noticia}, {"$set": doc}, upsert=True)
                    noticias_validas.append(doc)
                    links_ativos.append(url_noticia)
                else:
                    logger.info("   ❌ Não relevante - descartada")
        else:
            for i, url_noticia in enumerate(urls_noticias, start=1):
                logger.info(f"[{i}/{total_analisar}] Analisando: {url_noticia[:65]}...")
                try:
                    html_interna = None
                    try:
                        r_int = session.get(url_noticia, headers=HEADERS_PADRAO, timeout=15)
                        if r_int.status_code == 200:
                            html_interna = r_int.text
                    except Exception:
                        pass

                    if not html_interna:
                        if not driver:
                            driver = criar_navegador_headless()
                        driver.get(url_noticia)
                        time.sleep(2.5)
                        html_interna = driver.page_source

                    resultado = _analisar_html_noticia(url_noticia, html_interna)
                    if resultado["relevante"]:
                        doc = resultado["documento"]
                        dt_venc = resultado["data_vencimento"]
                        kws = resultado["palavras_chave"]

                        logger.info(f"   ✅ OPORTUNIDADE DETECTADA: {doc['titulo'][:75]}")
                        logger.info(f"   Palavras-chave: {', '.join(kws[:5])} | Categoria: {doc['categoria']}")
                        if dt_venc:
                            logger.info(f"   Prazo de inscrição detectado: {dt_venc.strftime('%d/%m/%Y')}")
                        else:
                            logger.info("   ℹ️ Oportunidade sem prazo específico detectado")

                        colecao.update_one({"link": url_noticia}, {"$set": doc}, upsert=True)
                        noticias_validas.append(doc)
                        links_ativos.append(url_noticia)
                    else:
                        logger.info("   ❌ Não relevante - descartada")
                except Exception as e:
                    logger.warning(f"   ⚠️ Erro ao processar {url_noticia[:50]}: {str(e)[:80]}")
                    continue

        # Passo 4: Remove apenas registros antigos que saíram da listagem atual
        if links_ativos:
            removidos = colecao.delete_many({"link": {"$nin": links_ativos}}).deleted_count
            if removidos > 0:
                logger.info(f"Limpeza concluída: {removidos} notícias antigas substituídas.")

            logger.info("=" * 70)
            logger.info(f"SUCESSO! oportunidades mineradas: {len(noticias_validas)} | Itens na base: {colecao.count_documents({})}")
            logger.info("=" * 70)

            logger.info("RESUMO DAS OPORTUNIDADES:")
            for i, noticia in enumerate(noticias_validas, start=1):
                venc_obj = noticia.get("data_vencimento")
                venc_str = venc_obj.strftime("%d/%m/%Y") if isinstance(venc_obj, datetime) else "Sem prazo"
                logger.info(f"  {i}. {noticia['nome'][:70]}... | {noticia['categoria']} | Prazo: {venc_str}")
        else:
            logger.warning("⚠️ Nenhuma oportunidade relevante encontrada nesta varredura.")

        return len(noticias_validas)

    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO NA MINERAÇÃO: {str(e)}", exc_info=True)
        return 0

    finally:
        session.close()
        if driver:
            logger.info("Fechando navegador...")
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    total = minerar_portal_uern()
    logger.info(f"Total de oportunidades mineradas: {total}")
