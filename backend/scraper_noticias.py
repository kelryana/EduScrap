##backend/scraper_noticias.py

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from base_scraper import configurar_log_scraper

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("scraper_noticias")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

# Fontes em formato RSS/Atom: (nome_feed, url, categoria_exibicao, fonte_exibicao, max_itens)
FONTES_RSS = [
    ("G1 Educação", "https://g1.globo.com/rss/g1/educacao/", "Notícia Educação", "G1", 8),
    ("G1 Saúde", "https://g1.globo.com/rss/g1/saude/", "Notícia Saúde", "G1", 8),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/educacao/feed.xml", "Notícia Educação", "Agência Brasil", 8),
    ("Agência Brasil - Geral", "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "Notícia Geral", "Agência Brasil", 8),
]


def coletar_rss(colecao, nome, url, categoria, fonte, limite, headers, vistos):
    """Coleta itens de um feed RSS/Atom e salva como notícia genérica."""
    total = 0
    try:
        resposta = requests.get(url, headers=headers, timeout=12)
        if resposta.status_code != 200:
            logger.warning(f"Status {resposta.status_code} no feed {nome}")
            return 0

        soup = BeautifulSoup(resposta.text, "xml")
        itens = soup.find_all("item") or soup.find_all("entry")

        for it in itens[:limite]:
            titulo_tag = it.find("title")
            link_tag = it.find("link")
            if not titulo_tag or not link_tag:
                continue

            titulo = titulo_tag.get_text(strip=True)
            link = link_tag.get_text(strip=True) or link_tag.get("href", "")

            if not titulo or not link or link in vistos:
                continue
            if "ufersa" in titulo.lower():
                continue  # Notícias UFERSA só na aba específica
            vistos.add(link)

            documento = {
                "nome": titulo,
                "titulo": titulo,
                "link": link,
                "categoria": categoria,
                "fonte": fonte,
                "tipo": "noticia",
                "coletado_em": datetime.now().isoformat(),
            }
            colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            total += 1
    except Exception as e:
        logger.error(f"Erro no feed {nome}: {e}")
    return total


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    return client[MONGODB_DB]["vagas_noticias"]


def atualizar_noticias_agora():
    logger.info("Iniciando raspagem ao vivo de múltiplas fontes (gerais + tech)...")
    colecao = conectar_banco()

    noticias_inseridas = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    vistos = set()

    # 1. Fontes gerais não-tech (Educação, Saúde, Geral) via RSS
    for nome, url, categoria, fonte, limite in FONTES_RSS:
        logger.info(f"-> Buscando no feed RSS: {nome}...")
        noticias_inseridas += coletar_rss(colecao, nome, url, categoria, fonte, limite, headers, vistos)

    try:
        logger.info("-> Buscando no G1 Tecnologia...")
        resposta_g1 = requests.get("https://g1.globo.com/tecnologia/", headers=headers, timeout=12)
        soup_g1 = BeautifulSoup(resposta_g1.text, 'html.parser')

        for post in soup_g1.find_all('div', class_='feed-post-body')[:10]:
            titulo_tag = post.find('a', class_='gui-color-hover')
            if not titulo_tag:
                continue

            link = titulo_tag.get('href')
            titulo = titulo_tag.text.strip()
            if not link or link in vistos or "ufersa" in titulo.lower():
                continue
            vistos.add(link)

            documento = {
                "nome": titulo,
                "titulo": titulo,
                "link": link,
                "categoria": "Notícia Tech",
                "fonte": "G1",
                "tipo": "noticia",
                "coletado_em": datetime.now().isoformat(),
            }
            colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            noticias_inseridas += 1
    except Exception as e:
        logger.error(f"Erro no G1: {e}")

    try:
        logger.info("-> Buscando no Canaltech...")
        resposta_ct = requests.get("https://canaltech.com.br/ultimas/", headers=headers, timeout=12)
        soup_ct = BeautifulSoup(resposta_ct.text, 'html.parser')

        titulos = soup_ct.find_all(['h3', 'h2'])
        ct_count = 0

        for titulo_tag in titulos:
            if ct_count >= 10:
                break

            link_tag = titulo_tag.find_parent('a')
            if not link_tag:
                continue

            link = link_tag.get('href', '')
            if link.startswith('/'):
                link = "https://canaltech.com.br" + link

            titulo = titulo_tag.text.strip()
            if not titulo or link in vistos or "ufersa" in titulo.lower():
                continue
            vistos.add(link)

            documento = {
                "nome": titulo,
                "titulo": titulo,
                "link": link,
                "categoria": "Notícia Tech",
                "fonte": "Canaltech",
                "tipo": "noticia",
                "coletado_em": datetime.now().isoformat(),
            }
            colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            noticias_inseridas += 1
            ct_count += 1

    except Exception as e:
        logger.error(f"Erro no Canaltech: {e}")

    if vistos:
        colecao.delete_many({"link": {"$nin": list(vistos)}})

    logger.info(f"Sucesso! salvos: {noticias_inseridas} | Itens na base: {colecao.count_documents({})}")
    return True


if __name__ == "__main__":
    configurar_log_scraper("noticias", "Notícias Tech (G1 e Canaltech)", "vagas_noticias")
    atualizar_noticias_agora()
