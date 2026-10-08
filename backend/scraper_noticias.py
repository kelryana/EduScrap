##backend/scraper_noticias.py 
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import logging
import os

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

def conectar_banco():
    client = MongoClient(MONGODB_URI)
    return client[MONGODB_DB]["vagas_noticias"]

def atualizar_noticias_agora():
    logger.info("\nIniciando raspagem ao vivo de múltiplas fontes...")
    colecao = conectar_banco()

    colecao.delete_many({})
    noticias_inseridas = 0
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        logger.info("-> Buscando no G1 Tecnologia...")
        resposta_g1 = requests.get("https://g1.globo.com/tecnologia/", headers=headers)
        soup_g1 = BeautifulSoup(resposta_g1.text, 'html.parser')

        for post in soup_g1.find_all('div', class_='feed-post-body')[:10]: # Pegando as 6 primeiras
            titulo_tag = post.find('a', class_='gui-color-hover')
            if not titulo_tag:
                continue

            documento = {
                "nome": titulo_tag.text.strip(),
                "link": titulo_tag.get('href'),
                "categoria": "Notícia Tech",
                "fonte": "G1"
            }
            colecao.insert_one(documento)
            noticias_inseridas += 1
    except Exception as e:
        logger.error(f"Erro no G1: {e}")

    try:
        logger.info("-> Buscando no Canaltech...")
        resposta_ct = requests.get("https://canaltech.com.br/ultimas/", headers=headers)
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

            documento = {
                "nome": titulo_tag.text.strip(),
                "link": link,
                "categoria": "Notícia Tech",
                "fonte": "Canaltech"
            }
            colecao.insert_one(documento)
            noticias_inseridas += 1
            ct_count += 1

    except Exception as e:
        logger.error(f"Erro no Canaltech: {e}")

    logger.info(f"Sucesso! {noticias_inseridas} notícias salvas no banco neste exato segundo.")
    return True

# Teste local
if __name__ == "__main__":
    atualizar_noticias_agora()