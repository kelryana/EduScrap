##backend/scraper_noticias.py

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
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

FUSO_BRASILIA = timezone(timedelta(hours=-3))

# Fontes em formato RSS/Atom: (nome_feed, url, categoria_exibicao, fonte_exibicao, max_itens)
FONTES_RSS = [
    ("G1 Educação", "https://g1.globo.com/rss/g1/educacao/", "Notícia Educação", "G1", 8),
    ("G1 Saúde", "https://g1.globo.com/rss/g1/saude/", "Notícia Saúde", "G1", 8),
    ("Agência Brasil", "https://agenciabrasil.ebc.com.br/rss/educacao/feed.xml", "Notícia Educação", "Agência Brasil", 8),
    ("Agência Brasil - Geral", "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml", "Notícia Geral", "Agência Brasil", 8),
    ("G1 Tecnologia", "https://g1.globo.com/rss/g1/tecnologia/", "Notícia Tech", "G1", 8),
    ("Canaltech", "https://canaltech.com.br/rss/", "Notícia Tech", "Canaltech", 8),
]


def extrair_data_hora_rss(item_tag):
    """Extrai data e hora explícitas do item RSS/Atom no fuso de Brasília (DD/MM/YYYY às HH:MM)."""
    for nome_tag in ("pubDate", "published", "updated", "dc:date", "date"):
        tag = item_tag.find(nome_tag)
        if tag and tag.get_text(strip=True):
            bruto = tag.get_text(strip=True)
            try:
                dt = parsedate_to_datetime(bruto)
                if dt.tzinfo is not None:
                    dt = dt.astimezone(FUSO_BRASILIA)
                return dt.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                pass
            try:
                dt = datetime.fromisoformat(bruto.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(FUSO_BRASILIA)
                return dt.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                pass
    return None


def coletar_rss(colecao, nome, url, categoria, fonte, limite, headers, vistos):
    """Coleta itens de um feed RSS/Atom e salva como notícia genérica com data e hora quando explícitas."""
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

            data_hora_pub = extrair_data_hora_rss(it)

            documento = {
                "nome": titulo,
                "titulo": titulo,
                "link": link,
                "categoria": categoria,
                "fonte": fonte,
                "tipo": "noticia",
                "coletado_em": datetime.now().isoformat(),
            }
            if data_hora_pub:
                documento["data_hora_publicacao"] = data_hora_pub

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

    # 1. Fontes gerais e tech via RSS (inclui pubDate com data e hora exatas sem sobrecarga)
    for nome, url, categoria, fonte, limite in FONTES_RSS:
        logger.info(f"-> Buscando no feed RSS: {nome}...")
        noticias_inseridas += coletar_rss(colecao, nome, url, categoria, fonte, limite, headers, vistos)

    # 2. Fallback HTML caso os feeds RSS de tecnologia não retornem itens suficientes
    if noticias_inseridas < 10:
        try:
            logger.info("-> Buscando no G1 Tecnologia (HTML fallback)...")
            resposta_g1 = requests.get("https://g1.globo.com/tecnologia/", headers=headers, timeout=12)
            soup_g1 = BeautifulSoup(resposta_g1.text, 'html.parser')

            for post in soup_g1.find_all('div', class_='feed-post-body')[:6]:
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

    if vistos:
        colecao.delete_many({"link": {"$nin": list(vistos)}})

    logger.info(f"Sucesso! salvos: {noticias_inseridas} | Itens na base: {colecao.count_documents({})}")
    return True


if __name__ == "__main__":
    configurar_log_scraper("noticias", "Notícias Tech (G1 e Canaltech)", "vagas_noticias")
    atualizar_noticias_agora()
