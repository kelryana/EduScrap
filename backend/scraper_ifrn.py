# backend/scraper_ifrn.py
"""
Scraper para o Portal de Processos Seletivos do IFRN (Instituto Federal do RN).
Captura editais de bolsas de ensino/pesquisa, projetos de extensão, transferências e seleções.
"""

import os
import re
import sys
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import urllib3
urllib3.disable_warnings()

# Garante import do normalizador semântico
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_ifrn")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_BUSCA_IFRN = "https://portal.ifrn.edu.br/processos-seletivos/buscar/"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["editais"]


def raspar_ifrn(paginas: int = 3):
    logger.info(f"Iniciando raspagem no IFRN (até {paginas} páginas)...")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    total_salvos = 0
    urls_processadas = set()

    for page in range(1, paginas + 1):
        url = f"{URL_BUSCA_IFRN}?page={page}"
        logger.info(f"Coletando página {page}: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            if resp.status_code != 200:
                logger.warning(f"IFRN retornou status {resp.status_code} na pág {page}")
                break
        except Exception as e:
            logger.error(f"Erro ao conectar com IFRN pág {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        h3_list = soup.find_all("h3")
        if not h3_list:
            break

        for h3 in h3_list:
            a = h3.find("a") or h3.find_parent("a")
            if not a or not a.get("href"):
                continue

            href = a["href"].strip()
            if not href.startswith("http"):
                href = "https://portal.ifrn.edu.br" + href

            if href in urls_processadas:
                continue
            urls_processadas.add(href)

            titulo = h3.get_text(strip=True)
            if not titulo or len(titulo) < 6:
                continue

            parent = h3.find_parent("div")
            snippet = parent.get_text(" ", strip=True) if parent else titulo

            # Extração de número do edital
            edital_num = None
            match_edital = re.search(r"edital:\s*([0-9\/\.\-]+(?:\s*-\s*[A-Z\/]+)?)", snippet, re.IGNORECASE)
            if match_edital:
                edital_num = match_edital.group(1).strip()

            # Extração do campus / local limpo
            campus_str = "IFRN"
            match_campus = re.search(r"seleção para:\s*([^,\n\r]+?)(?:\s*(?:link|Ver processo|arrow_forward_ios|\d|article|Edital)|$)", snippet, re.IGNORECASE)
            if match_campus:
                local_limpo = match_campus.group(1).strip()
                if local_limpo and len(local_limpo) < 30:
                    campus_str = f"IFRN ({local_limpo})"

            # Classificação semântica automática
            classificacao = classificar_oportunidade(titulo, snippet)
            cursos = classificacao["cursos"]
            areas = classificacao["areas"] or ["Educação", "Universitário"]

            data_pub = datetime.now().strftime("%Y-%m-%d")

            documento = {
                "titulo": f"[{campus_str}] {titulo}",
                "nome": f"[{campus_str}] {titulo}",
                "descricao": snippet[:400] if snippet else titulo,
                "link": href,
                "url": href,
                "fonte": campus_str,
                "tipo": "edital",
                "categoria": "Bolsas e Projetos",
                "status": "Aberto",
                "data_publicacao": data_pub,
                "cursos": cursos,
                "areas": areas,
                "geral": classificacao["geral"],
                "coletado_em": datetime.now().isoformat()
            }
            if edital_num:
                documento["edital_numero"] = edital_num

            res = colecao.update_one(
                {"link": href},
                {"$set": documento},
                upsert=True
            )

            if res.upserted_id or res.modified_count > 0:
                total_salvos += 1
                logger.info(f"-> Salvo IFRN: {titulo[:50]} | Local: {campus_str} | Cursos: {cursos}")

    logger.info(f"Finalizado IFRN! {total_salvos} oportunidades processadas/atualizadas.")
    return total_salvos


if __name__ == "__main__":
    raspar_ifrn()
