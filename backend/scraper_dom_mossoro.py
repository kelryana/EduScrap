# backend/scraper_dom_mossoro.py

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
logger = logging.getLogger("scraper_dom_mossoro")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")
URL_ATOS_DOM = "http://dom.mossoro.rn.gov.br/dom/atos"


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["editais"]


def raspar_dom_mossoro(paginas: int = 3):
    logger.info(f"=== INICIANDO RASPAGEM DO DIÁRIO OFICIAL DE MOSSORÓ (DOM) ===")
    colecao = conectar_banco()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    total_salvos = 0
    atos_processados = set()

    for page in range(1, paginas + 1):
        url = f"{URL_ATOS_DOM}?page={page}" if page > 1 else URL_ATOS_DOM
        logger.info(f"Coletando atos da página {page}: {url}")

        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"Status HTTP {resp.status_code} na página {page} do DOM")
                break
        except Exception as e:
            logger.error(f"Erro ao conectar com DOM Mossoró: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        links_atos = soup.find_all("a", href=lambda h: h and "/dom/ato/" in h)

        for a in links_atos:
            href = a["href"].strip()
            if href in atos_processados:
                continue
            atos_processados.add(href)

            url_ato = f"http://dom.mossoro.rn.gov.br{href}"

            # Coleta o conteúdo detalhado do ato
            try:
                resp_ato = requests.get(url_ato, headers=headers, timeout=10)
                if resp_ato.status_code != 200:
                    continue
                soup_ato = BeautifulSoup(resp_ato.text, "html.parser")

                h3 = soup_ato.find("h3")
                titulo = h3.get_text(strip=True) if h3 else a.get_text(strip=True)

                # Busca corpo do texto
                ps = [p.get_text(" ", strip=True) for p in soup_ato.find_all("p") if len(p.get_text(strip=True)) > 40]
                texto_ato = " ".join(ps) if ps else titulo

                # Filtra se é relevante para universitários (editais, seleções, convocações, cultura, educação, saúde)
                palavras_chave = [
                    "edital", "processo seletivo", "seleção", "estágio", "estagiário",
                    "bolsa", "convocação", "fomento", "pnab", "assistência", "inscriç"
                ]
                texto_lower = (titulo + " " + texto_ato).lower()
                if not any(k in texto_lower for k in palavras_chave):
                    continue

                # Extração de número do edital se houver
                match_edital = re.search(r"edital\s*(?:n[ºo°]?\s*)?([0-9\/\.\-]+(?:\s*-\s*[A-Z\/]+)?)", texto_lower, re.IGNORECASE)
                edital_num = match_edital.group(1).strip() if match_edital else None

                # Extração da secretaria
                secretaria = "Prefeitura de Mossoró"
                match_sec = re.search(r"(secretaria municipal de [a-zçãéíóú\s]+|gabinete do prefeito)", texto_lower)
                if match_sec:
                    secretaria = match_sec.group(1).title()

                classificacao = classificar_oportunidade(titulo, texto_ato)
                cursos = classificacao["cursos"]
                areas = classificacao["areas"] or ["Processos Seletivos", "Setor Público"]

                documento = {
                    "titulo": f"[DOM/Mossoró] {titulo}",
                    "nome": f"[DOM/Mossoró] {titulo}",
                    "descricao": texto_ato[:450] if texto_ato else titulo,
                    "link": url_ato,
                    "url": url_ato,
                    "fonte": f"Prefeitura de Mossoró ({secretaria})",
                    "tipo": "edital",
                    "categoria": "Editais Municipais",
                    "status": "Aberto",
                    "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
                    "cursos": cursos,
                    "areas": areas,
                    "geral": classificacao["geral"],
                    "coletado_em": datetime.now().isoformat()
                }
                if edital_num:
                    documento["edital_numero"] = edital_num

                res = colecao.update_one({"link": url_ato}, {"$set": documento}, upsert=True)
                if res.upserted_id or res.modified_count > 0:
                    total_salvos += 1
                    logger.info(f"-> Salvo DOM: {titulo[:60]}... | Órgão: {secretaria}")

            except Exception as e_ato:
                logger.error(f"Erro ao processar ato {url_ato}: {e_ato}")
                continue

    logger.info(f"=== DOM MOSSORÓ CONCLUÍDO! {total_salvos} editais salvos/atualizados. ===")
    return total_salvos


if __name__ == "__main__":
    raspar_dom_mossoro()
