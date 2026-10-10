# backend/scraper_cpps_ufersa.py
"""
Scraper para o portal CPPS da UFERSA (Comissão Permanente de Processos Seletivos).
Captura editais de processos seletivos, vagas ociosas, transferências e seleções acadêmicas.
"""

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

# Garante path para módulos internos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_cpps_ufersa")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_BASE_CPPS = "https://cpps.ufersa.edu.br/"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["editais"]


def extrair_data_edital(texto: str):
    if not texto:
        return None
    padroes = [
        r"(\d{1,2})\s+de\s+([a-zA-Zç]+)\s+de\s+(\d{4})",
        r"(\d{1,2})\s+([a-zA-Zç]+),\s*(\d{4})",
        r"(\d{2})/(\d{2})/(\d{4})"
    ]
    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
        "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
        "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
        "mai": 5, "jan": 1, "fev": 2, "mar": 3, "abr": 4, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            g = match.groups()
            if len(g) == 3:
                try:
                    if g[1].isdigit():
                        return f"{g[2]}-{int(g[1]):02d}-{int(g[0]):02d}"
                    mes_nome = g[1].lower()
                    mes_num = meses.get(mes_nome)
                    if mes_num:
                        return f"{g[2]}-{mes_num:02d}-{int(g[0]):02d}"
                except Exception:
                    continue
    return None


def raspar_cpps():
    logger.info(f"Iniciando raspagem no CPPS UFERSA: {URL_BASE_CPPS}")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(URL_BASE_CPPS, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            logger.error(f"Erro HTTP {resp.status_code} ao acessar {URL_BASE_CPPS}")
            return 0
    except Exception as e:
        logger.error(f"Falha de conexão com CPPS UFERSA: {e}")
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    posts_processados = set()
    total_salvos = 0

    for a in soup.find_all("a"):
        href = a.get("href", "")
        titulo = a.get_text(strip=True)

        if not href or "cpps.ufersa.edu.br/202" not in href or not titulo or len(titulo) < 10:
            continue

        if href in posts_processados:
            continue
        posts_processados.add(href)

        # Busca bloco circundante para obter texto e data
        parent = a.find_parent(["div", "article", "li"])
        snippet = parent.get_text(" ", strip=True) if parent else ""

        data_pub = extrair_data_edital(snippet) or datetime.now().strftime("%Y-%m-%d")

        # Classifica cursos e áreas
        classificacao = classificar_oportunidade(titulo, snippet)
        cursos = classificacao["cursos"]
        areas = classificacao["areas"] or ["Processos Seletivos", "Universitário"]

        documento = {
            "titulo": f"[CPPS/UFERSA] {titulo}",
            "nome": f"[CPPS/UFERSA] {titulo}",
            "descricao": snippet[:350] if snippet else titulo,
            "link": href,
            "url": href,
            "fonte": "UFERSA (CPPS)",
            "tipo": "edital",
            "categoria": "Processos Seletivos",
            "status": "Aberto",
            "data_publicacao": data_pub,
            "cursos": cursos,
            "areas": areas,
            "geral": classificacao["geral"],
            "coletado_em": datetime.now().isoformat()
        }

        # Extrai número do edital se houver
        match_edital = re.search(r"edital\s*(?:n[ºo°]?\s*)?([0-9\/\.\-]+)", titulo, re.IGNORECASE)
        if match_edital:
            documento["edital_numero"] = match_edital.group(1)

        res = colecao.update_one(
            {"link": href},
            {"$set": documento},
            upsert=True
        )

        if res.upserted_id or res.modified_count > 0:
            total_salvos += 1
            logger.info(f"-> Salvo CPPS: {titulo[:60]}... | Cursos: {cursos} | Áreas: {areas}")

    logger.info(f"Finalizado CPPS UFERSA! {total_salvos} oportunidades processadas/atualizadas.")
    return total_salvos


if __name__ == "__main__":
    raspar_cpps()
