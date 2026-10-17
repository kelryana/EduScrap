##backend/scraper_ufersa.py

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

class ScraperUFERSA(BaseScraper):
    """Scraper oficial da UFERSA em conformidade com BaseScraper (RNF05)"""
    def __init__(self):
        super().__init__(
            nome_fonte="UFERSA",
            url_base="https://proae.ufersa.edu.br/",
            nome_colecao="vagas_ufersa"
        )
        self.paginas_alvo = [
            "https://proae.ufersa.edu.br/editais/",
            "https://proae.ufersa.edu.br/categoria/editais-abertos/"
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
                artigos = soup.find_all(['article', 'div'], class_=re.compile(r'post|entry|edital'))
                for art in artigos:
                    tag_a = art.find('a')
                    if not tag_a:
                        continue
                    nome = self.limpar_texto(tag_a.get_text(strip=True))
                    href = tag_a.get('href')
                    if not href or not href.startswith("http") or len(nome) < 5:
                        continue
                    dt = extrair_data_vencimento(nome) or extrair_data_vencimento_datetime(nome, href)
                    doc = {
                        "nome": nome,
                        "titulo": nome,
                        "link": href,
                        "categoria": "Assistência Estudantil",
                        "fonte": "UFERSA"
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
    return db["vagas_ufersa"]

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

def raspar_lista_ufersa(url_menu, ano_filtro, colecao_bd):
    logger.info(f"Passo 1: Acessando o menu da UFERSA: {url_menu} (Filtro: {ano_filtro})")
    headers = {'User-Agent': 'Mozilla/5.0'}

    resposta_menu = requests.get(url_menu, headers=headers)
    if resposta_menu.status_code != 200:
        logger.info("Erro ao acessar a página de lista.")
        return

    soup_menu = BeautifulSoup(resposta_menu.text, 'html.parser')

    links_visitados = set()
    editais_inseridos = 0

    for tag_a in soup_menu.find_all('a'):
        texto_link = tag_a.get_text(strip=True)
        url_edital = tag_a.get('href')

        if not url_edital or url_edital == "#" or not url_edital.startswith("http"):
            continue

        if texto_link.lower().startswith("edital") and ano_filtro in texto_link:

            if url_edital not in links_visitados:
                links_visitados.add(url_edital)
                logger.info(f"\n-> Encontrou: {texto_link[:50]}...")

                try:
                    resposta_edital = requests.get(url_edital, headers=headers)
                    soup_edital = BeautifulSoup(resposta_edital.text, 'html.parser')

                    nome_edital = texto_link
                    link_pdf = url_edital

                    for a_pdf in soup_edital.find_all('a'):
                        texto_pdf = a_pdf.get_text(strip=True).upper()
                        href_pdf = a_pdf.get('href', '')

                        if "EDITAL" in texto_pdf and "wp-content/uploads" in href_pdf:
                            link_pdf = href_pdf
                            break

                    data_vencimento = extrair_data_vencimento(nome_edital)

                    if not data_vencimento:
                        # Procura o prazo no texto da página do edital e, depois, no PDF
                        texto_pagina = soup_edital.get_text(" ", strip=True)
                        data_vencimento = extrair_data_vencimento_datetime(texto_pagina, link_pdf)

                    documento = {
                        "nome": nome_edital,
                        "link": link_pdf,
                        "categoria": "Auxílio/Bolsa",
                        "fonte": "UFERSA"
                    }

                    if data_vencimento:
                        documento["data_vencimento"] = data_vencimento

                    # Update the record based on the name
                    result = colecao_bd.update_one(
                        {"nome": nome_edital},
                        {"$set": documento},
                        upsert=True
                    )
                    if result.upserted_id or result.modified_count > 0:
                        editais_inseridos += 1
                        logger.info("   [Salvo no banco com sucesso]")

                except Exception as e:
                    logger.info(f"   [Erro ao ler a página do edital: {e}]")

    logger.info(f"\nFinalizado! {editais_inseridos} editais da UFERSA salvos.")

if __name__ == "__main__":
    colecao = conectar_banco()

    url_alvo = "https://proae.ufersa.edu.br/"
    ano_desejado = "2026"

    raspar_lista_ufersa(url_alvo, ano_desejado, colecao)
    
    # Try alternative URLs if needed
    try:
        raspar_lista_ufersa("https://proae.ufersa.edu.br/2026-2/", ano_desejado, colecao)
    except Exception as e:
        logger.error(f"Erro ao tentar URL alternativa: {e}")