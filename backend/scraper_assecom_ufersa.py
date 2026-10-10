# backend/scraper_assecom_ufersa.py

import os
import re
import sys
import logging
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import urllib3
urllib3.disable_warnings()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_assecom_ufersa")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_BASE_ASSECOM = "https://assecom.ufersa.edu.br/"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["noticias"]


def raspar_assecom():
    logger.info(f"Iniciando raspagem na ASSECOM UFERSA: {URL_BASE_ASSECOM}")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(URL_BASE_ASSECOM, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            logger.error(f"Erro HTTP {resp.status_code} ao acessar {URL_BASE_ASSECOM}")
            return 0
    except Exception as e:
        logger.error(f"Falha de conexão com ASSECOM UFERSA: {e}")
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    posts_processados = set()
    total_salvos = 0

    for a in soup.find_all("a"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)

        if not href or "assecom.ufersa.edu.br/202" not in href or not titulo or len(titulo) < 15:
            continue

        if href in posts_processados:
            continue
        posts_processados.add(href)

        # Busca resumo ou texto ao redor
        parent = a.find_parent(["div", "article", "li"])
        snippet = parent.get_text(" ", strip=True) if parent else ""

        # Extrai data da URL (ex: 2026/10/08)
        data_match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", href)
        if data_match:
            data_pub = f"{data_match.group(1)}-{data_match.group(2)}-{data_match.group(3)}"
        else:
            data_pub = datetime.now().strftime("%Y-%m-%d")

        # Classifica
        classificacao = classificar_oportunidade(titulo, snippet)
        cursos = classificacao["cursos"]
        areas = classificacao["areas"] or ["Notícias Acadêmicas", "Universitário"]

        documento = {
            "titulo": titulo,
            "descricao": snippet[:350] if snippet else titulo,
            "resumo": snippet[:200] if snippet else titulo,
            "link": href,
            "url": href,
            "fonte": "UFERSA (ASSECOM)",
            "tipo": "noticia",
            "categoria": "Comunicação Universitária",
            "data_publicacao": data_pub,
            "cursos": cursos,
            "areas": areas,
            "coletado_em": datetime.now().isoformat()
        }

        res = colecao.update_one(
            {"link": href},
            {"$set": documento},
            upsert=True
        )

        if res.upserted_id or res.modified_count > 0:
            total_salvos += 1
            logger.info(f"-> Salvo ASSECOM: {titulo[:60]}... | Cursos: {cursos} | Áreas: {areas}")

    logger.info(f"Finalizado ASSECOM UFERSA! {total_salvos} notícias processadas/atualizadas.")
    return total_salvos


if __name__ == "__main__":
    raspar_assecom()
