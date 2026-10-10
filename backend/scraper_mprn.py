# backend/scraper_mprn.py

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

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_mprn")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_BASE_MPRN = "https://www.mprn.mp.br/category/selecao/"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["vagas"]


def raspar_mprn():
    logger.info(f"Iniciando raspagem no MPRN Seleções: {URL_BASE_MPRN}")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(URL_BASE_MPRN, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200:
            logger.error(f"Erro HTTP {resp.status_code} ao acessar {URL_BASE_MPRN}")
            return 0
    except Exception as e:
        logger.error(f"Falha de conexão com MPRN: {e}")
        return 0

    soup = BeautifulSoup(resp.text, "html.parser")
    posts_processados = set()
    total_salvos = 0

    for h in soup.find_all(["h2", "h3", "h4"]):
        a = h.find("a")
        if not a:
            continue

        href = a.get("href", "")
        titulo = a.get_text(strip=True)

        if not href or "mprn.mp.br/noticias/" not in href or not titulo or len(titulo) < 15:
            continue

        if href in posts_processados:
            continue
        posts_processados.add(href)

        # Contexto/descrição
        parent = h.find_parent(["article", "div"])
        snippet = parent.get_text(" ", strip=True) if parent else ""

        # Extração inteligente da data limite de inscrição do texto
        meses_pt = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        data_vencimento = None
        status_vaga = "Aberto"

        padroes_prazo = [
            r"(?:entre\s+os\s+dias\s+\d+\s+e\s+|de\s+\d+\s+a\s+|a\s+|até\s+(?:o\s+dia\s+)?|às\s+\d+h\s+de\s+)(\d{1,2})(?:º)?\s+de\s+([a-zA-Zç]+)(?:\s+de\s+(\d{4}))?",
            r"(\d{1,2})\s+de\s+([a-zA-Zç]+)(?:\s+de\s+(\d{4}))?"
        ]
        texto_analise = f"{titulo} {snippet}"
        for padrao in padroes_prazo:
            matches = re.findall(padrao, texto_analise, re.IGNORECASE)
            if matches:
                dia_str, mes_str, ano_str = matches[-1]
                mes_num = meses_pt.get(mes_str.lower())
                if mes_num:
                    ano_num = int(ano_str) if ano_str else 2026
                    try:
                        data_vencimento = datetime(ano_num, mes_num, int(dia_str))
                        if data_vencimento.date() < datetime.now().date():
                            status_vaga = "Encerrado"
                        else:
                            status_vaga = "Aberto"
                        break
                    except Exception:
                        pass

        # Classifica cursos e áreas
        classificacao = classificar_oportunidade(titulo, snippet)
        cursos = classificacao["cursos"]
        areas = classificacao["areas"] or ["Judiciário", "Serviço Público"]

        documento = {
            "titulo": f"[MPRN] {titulo}",
            "descricao": snippet[:350] if snippet else titulo,
            "resumo": snippet[:200] if snippet else titulo,
            "link": href,
            "url": href,
            "fonte": "MPRN (Ministério Público do RN)",
            "tipo": "vaga",
            "categoria": "Estágios MPRN",
            "status": status_vaga,
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "cursos": cursos,
            "areas": areas,
            "cidade": "Mossoró / RN",
            "coletado_em": datetime.now().isoformat()
        }

        if data_vencimento:
            documento["data_vencimento"] = data_vencimento
            documento["data_vencimento_formatada"] = data_vencimento.strftime("%d/%m/%Y")
            dias_rest = (data_vencimento.date() - datetime.now().date()).days
            documento["dias_restantes"] = dias_rest
            documento["status_prazo"] = "vigente" if dias_rest >= 0 else "vencido"

        res = colecao.update_one(
            {"link": href},
            {"$set": documento},
            upsert=True
        )

        if res.upserted_id or res.modified_count > 0:
            total_salvos += 1
            logger.info(f"-> Salvo MPRN: {titulo[:60]}... | Cursos: {cursos} | Áreas: {areas}")

    logger.info(f"Finalizado MPRN! {total_salvos} processos seletivos processados/atualizados.")
    return total_salvos


if __name__ == "__main__":
    raspar_mprn()
