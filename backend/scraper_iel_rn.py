# backend/scraper_iel_rn.py

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

# Garante import do classificador semântico
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_iel_rn")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_VAGAS_IEL = "https://ielrn.empregare.com/pt-br/vagas"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["vagas"]


def raspar_iel():
    logger.info(f"Iniciando raspagem no IEL/RN: {URL_VAGAS_IEL}")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(URL_VAGAS_IEL, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            logger.error(f"Erro HTTP {resp.status_code} ao acessar {URL_VAGAS_IEL}")
            return 0
    except Exception as e:
        logger.error(f"Falha de conexão com IEL/RN: {e}")
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("a:has(.card-vaga)")
    total_salvos = 0

    for a in cards:
        href = a.get("href", "")
        if not href.startswith("http"):
            link_completo = f"https://ielrn.empregare.com{href}"
        else:
            link_completo = href

        card = a.select_one(".card-vaga")
        if not card:
            continue

        titulo_elem = card.select_one(".titulo-vaga")
        titulo = titulo_elem.get_text(strip=True) if titulo_elem else ""
        if not titulo:
            continue

        empresa_elem = card.select_one(".card-vaga-empresa")
        empresa = empresa_elem.get_text(strip=True) if empresa_elem else "IEL / FIERN"

        data_elem = card.select_one(".card-vaga-data")
        data_texto = data_elem.get_text(strip=True) if data_elem else ""

        snippet = card.get_text(" ", strip=True)

        # Classificação de curso e área
        classificacao = classificar_oportunidade(titulo, snippet)
        cursos = classificacao["cursos"]
        areas = classificacao["areas"] or ["Estágio", "Mercado de Trabalho"]

        documento = {
            "titulo": f"[IEL/RN] {titulo}",
            "nome": f"[IEL/RN] {titulo}",
            "descricao": snippet[:400] if snippet else titulo,
            "link": link_completo,
            "url": link_completo,
            "fonte": "IEL / FIERN",
            "tipo": "estagio",
            "categoria": "Estágios & Mercado",
            "empresa": empresa,
            "status": "Aberto",
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "data_texto": data_texto,
            "cursos": cursos,
            "areas": areas,
            "geral": classificacao["geral"],
            "coletado_em": datetime.now().isoformat()
        }

        res = colecao.update_one(
            {"link": link_completo},
            {"$set": documento},
            upsert=True
        )

        if res.upserted_id or res.modified_count > 0:
            total_salvos += 1
            logger.info(f"-> Salvo IEL/RN: {titulo} | Cursos: {cursos} | Áreas: {areas}")

    logger.info(f"Finalizado IEL/RN! {total_salvos} vagas processadas/atualizadas.")
    return total_salvos


if __name__ == "__main__":
    raspar_iel()
