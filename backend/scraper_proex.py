##backend/scraper_proex.py

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from pdf_utils import extrair_data_vencimento_datetime
from base_scraper import BaseScraper
# Carrega variáveis de ambiente do .env na raiz do projeto
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

class ScraperPROEX(BaseScraper):
    """Scraper oficial da PROEX/UERN em conformidade com BaseScraper (RNF05)"""
    def __init__(self):
        super().__init__(
            nome_fonte="PROEX/UERN",
            url_base="https://portal.uern.br/proex/",
            nome_colecao="vagas_bolsa"
        )
        self.paginas_alvo = [
            "https://portal.uern.br/proex/2026-2/",
            "https://portal.uern.br/proex/",
            "https://portal.uern.br/proex/2026/",
            "https://portal.uern.br/proex/editais/"
        ]

    def coletar(self):
        itens_totais = []
        for url in self.paginas_alvo:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                res = requests.get(url, headers=headers, timeout=20)
                if res.status_code != 200:
                    continue
                soup = BeautifulSoup(res.text, 'html.parser')
                for ul in soup.find_all('ul'):
                    if ul.find_parent(['nav', 'aside', 'footer', 'header']):
                        continue
                    elemento_cat = ul.find_previous_sibling(['p', 'h2', 'h3', 'h4', 'strong'])
                    cat_texto = elemento_cat.get_text(strip=True) if elemento_cat else "Categoria Geral"
                    for li in ul.find_all('li'):
                        tag_a = li.find('a')
                        if not tag_a:
                            continue
                        bruto = li.get_text(strip=True)
                        href = tag_a.get('href')
                        if not bruto.lower().startswith("edital") or not href or not href.startswith("http"):
                            continue
                        nome = self.limpar_texto(bruto.replace("(Clique Aqui)", "").replace("(Clique aqui)", ""))
                        if nome.endswith("-"):
                            nome = nome[:-1].strip()
                        dt = extrair_data_vencimento(bruto) or extrair_data_vencimento(f"{nome} {cat_texto}")
                        if not dt:
                            dt = extrair_data_vencimento_datetime(bruto, href)
                        doc = {
                            "nome": nome,
                            "titulo": nome,
                            "link": href,
                            "categoria": cat_texto,
                            "fonte": "PROEX/UERN"
                        }
                        if dt:
                            doc["data_vencimento"] = dt
                        itens_totais.append(doc)
            except Exception as e:
                self.logger.warning(f"Erro ao coletar {url}: {e}")
        return itens_totais


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["vagas_bolsa"]

def extrair_data_vencimento(texto):
    if not texto:
        return None

    padroes = [
        r"\b(\d{2})/(\d{2})/(\d{4})\b",
        r"\b(\d{1,2})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{4})\b",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            try:
                dia, mes, ano = int(match.group(1)), int(match.group(2)), int(match.group(3))
                data = datetime(ano, mes, dia)
                return data
            except ValueError:
                continue
    return None

def raspar_pagina_proex(url, colecao_bd):
    logger.info(f"Acessando a página da PROEX: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    resposta = requests.get(url, headers=headers)

    if resposta.status_code != 200:
        logger.error(f"Erro ao acessar a página. Código: {resposta.status_code}")
        return

    soup = BeautifulSoup(resposta.text, 'html.parser')
    editais_inseridos = 0

    for tag_link in soup.find_all('a'):
        if tag_link.find_parent(['nav', 'aside', 'footer', 'header']):
            continue

        texto_link = tag_link.get_text(strip=True).upper()

        if texto_link == "EDITAL":
            link_pdf = tag_link.get('href')

            if not link_pdf or link_pdf == "#" or not link_pdf.startswith("http"):
                continue

            parent = tag_link.parent
            container = parent.parent if parent.name == 'li' else parent

            irmao = container.find_previous_sibling()
            texto_titulo = ""

            while irmao:
                texto_temp = irmao.get_text(strip=True)
                if texto_temp:
                    texto_titulo = texto_temp
                    break
                irmao = irmao.find_previous_sibling()

            if not texto_titulo.upper().startswith("EDITAL"):
                continue

            nome_edital = texto_titulo.strip()

            data_vencimento = extrair_data_vencimento(nome_edital)

            if not data_vencimento:
                texto_completo = f"{nome_edital} Bolsa"
                data_vencimento = extrair_data_vencimento(texto_completo)

            if not data_vencimento:
                # Título raramente traz o prazo: lê o PDF do edital
                data_vencimento = extrair_data_vencimento_datetime(nome_edital, link_pdf)

            documento = {
                "nome": nome_edital,
                "link": link_pdf,
                "categoria": "Bolsa",
                "fonte": "PROEX/UERN"
            }

            if data_vencimento:
                documento["data_vencimento"] = data_vencimento

            # Update the record based on the link
            result = colecao_bd.update_one(
                {"link": link_pdf},
                {"$set": documento},
                upsert=True
            )
            if result.upserted_id or result.modified_count > 0:
                editais_inseridos += 1

    logger.info(f"Sucesso! {editais_inseridos} editais de Bolsa (PROEX) processados.\n")

if __name__ == "__main__":
    colecao = conectar_banco()

    # Lista de páginas alvo da PROEX
    paginas_alvo_proex = [
        "https://portal.uern.br/proex/2026-2/",
        "https://portal.uern.br/proex/",
        "https://portal.uern.br/proex/2026/",
        "https://portal.uern.br/proex/editais/"
    ]

    for pagina in paginas_alvo_proex:
        try:
            raspar_pagina_proex(pagina, colecao)
        except Exception as e:
            logger.error(f"Erro ao processar a página {pagina}: {e}")

    logger.info("Finalizado! Verifique o MongoDB Compass.")