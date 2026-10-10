# backend/scraper_capacitacao_bolsas.py
"""
Scraper para Oportunidades de Capacitação, Certificações Gratuitas e Bolsas de Estudo.
Fontes integradas:
1. DIO.me (Artigos técnicos, bootcamps e capacitação de tecnologia comunitária)
2. Estudar Fora / Fundação Estudar (Bolsas internacionais de graduação, pós, STEM e mobilidade acadêmica)
3. Escola do Trabalhador 4.0 / Ministério do Trabalho e Microsoft (Cursos gratuitos de IA e TI com certificado)
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

# Garante import do classificador semântico
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("scraper_capacitacao_bolsas")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")


def conectar_banco():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    return db["noticias"]


def raspar_estudar_fora(colecao):
    logger.info("-> Coletando bolsas do portal Estudar Fora (Fundação Estudar)...")
    url = "https://www.estudarfora.org.br/feed/"
    headers = {"User-Agent": "Mozilla/5.0"}
    total = 0

    try:
        resp = requests.get(url, headers=headers, timeout=12, verify=False)
        if resp.status_code != 200:
            logger.warning(f"Status {resp.status_code} ao acessar {url}")
            return 0

        soup = BeautifulSoup(resp.text, "xml")
        for it in soup.find_all("item"):
            titulo = it.title.get_text(strip=True) if it.title else ""
            link = it.link.get_text(strip=True) if it.link else ""
            desc_raw = it.description.get_text(strip=True) if it.description else ""
            snippet = BeautifulSoup(desc_raw, "html.parser").get_text(" ", strip=True)

            if not titulo or not link:
                continue

            classificacao = classificar_oportunidade(titulo, snippet)
            cursos = classificacao["cursos"]
            areas = classificacao["areas"] or ["Bolsas de Estudo", "Capacitação"]

            documento = {
                "titulo": f"[Bolsa Internacional] {titulo}",
                "nome": f"[Bolsa Internacional] {titulo}",
                "descricao": snippet[:400] if snippet else titulo,
                "link": link,
                "url": link,
                "fonte": "Fundação Estudar / Estudar Fora",
                "tipo": "bolsa_estudo",
                "categoria": "Bolsas de Estudos",
                "status": "Aberto",
                "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
                "cursos": cursos,
                "areas": areas,
                "geral": classificacao["geral"],
                "coletado_em": datetime.now().isoformat()
            }

            res = colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            if res.upserted_id or res.modified_count > 0:
                total += 1
                logger.info(f"   Salvo Estudar Fora: {titulo[:50]}... | Cursos: {cursos}")

    except Exception as e:
        logger.error(f"Erro ao coletar Estudar Fora: {e}")

    return total


def raspar_dio(colecao):
    logger.info("-> Coletando capacitações e artigos da Digital Innovation One (DIO)...")
    url = "https://www.dio.me/articles"
    headers = {"User-Agent": "Mozilla/5.0"}
    total = 0

    try:
        resp = requests.get(url, headers=headers, timeout=12, verify=False)
        if resp.status_code != 200:
            return 0

        soup = BeautifulSoup(resp.text, "html.parser")
        processados = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("/articles/") or "/tecnologia/" in href:
                continue

            titulo = a.get_text(strip=True)
            if not titulo or len(titulo) < 15 or titulo in processados:
                continue
            processados.add(titulo)

            link_completo = f"https://www.dio.me{href}"
            classificacao = classificar_oportunidade(titulo, "Capacitação e desenvolvimento em tecnologia e IA")
            cursos = classificacao["cursos"] or ["Ciência da Computação", "Engenharia de Software"]
            areas = ["Tecnologia", "Capacitação & Cursos"]

            documento = {
                "titulo": f"[DIO Tech] {titulo}",
                "nome": f"[DIO Tech] {titulo}",
                "descricao": f"Conteúdo formativo de tecnologia e inteligência artificial da comunidade DIO: {titulo}.",
                "link": link_completo,
                "url": link_completo,
                "fonte": "Digital Innovation One (DIO)",
                "tipo": "capacitacao",
                "categoria": "Capacitação & Cursos",
                "status": "Aberto",
                "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
                "cursos": cursos,
                "areas": areas,
                "geral": False,
                "coletado_em": datetime.now().isoformat()
            }

            res = colecao.update_one({"link": link_completo}, {"$set": documento}, upsert=True)
            if res.upserted_id or res.modified_count > 0:
                total += 1
                logger.info(f"   Salvo DIO: {titulo[:50]}...")
            if total >= 8:
                break

    except Exception as e:
        logger.error(f"Erro ao coletar DIO: {e}")

    return total


def adicionar_trilhas_ministerio_trabalho(colecao):
    logger.info("-> Cadastrando trilhas oficiais gratuitas da Escola do Trabalhador 4.0 (MTE / Microsoft)...")
    trilhas = [
        {
            "titulo": "[MEC/MTE] Inteligência Artificial e Produtividade com Microsoft",
            "descricao": "Curso gratuito oficial do Ministério do Trabalho e Emprego em parceria com a Microsoft com certificado reconhecido em IA generativa.",
            "link": "https://escoladotrabalhador40.com.br",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Administração"],
            "areas": ["Tecnologia", "Inovação", "Capacitação & Cursos"]
        },
        {
            "titulo": "[MEC/MTE] Alfabetização Digital e Computação em Nuvem (Cloud)",
            "descricao": "Capacitação gratuita de fundamentos da nuvem Azure para universitários iniciantes em computação e negócios.",
            "link": "https://escoladotrabalhador40.com.br",
            "cursos": ["Ciência da Computação", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[MEC/MTE] Análise de Dados e Power BI para Tomada de Decisão",
            "descricao": "Trilha prática com certificado de formação em Business Intelligence e tratamento de dados para universitários de exatas e gestão.",
            "link": "https://escoladotrabalhador40.com.br",
            "cursos": ["Administração", "Ciências Contábeis", "Ciência da Computação"],
            "areas": ["Exatas", "Tecnologia", "Capacitação & Cursos"]
        }
    ]

    total = 0
    for t in trilhas:
        doc = {
            "titulo": t["titulo"],
            "nome": t["titulo"],
            "descricao": t["descricao"],
            "link": t["link"],
            "url": t["link"],
            "fonte": "Ministério do Trabalho / Microsoft",
            "tipo": "capacitacao",
            "categoria": "Capacitação & Cursos",
            "status": "Aberto",
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "cursos": t["cursos"],
            "areas": t["areas"],
            "geral": False,
            "coletado_em": datetime.now().isoformat()
        }
        res = colecao.update_one({"titulo": t["titulo"]}, {"$set": doc}, upsert=True)
        if res.upserted_id or res.modified_count > 0:
            total += 1
            logger.info(f"   Salvo MTE: {t['titulo']}")

    return total


def raspar_todas_capacitacoes():
    logger.info("=== INICIANDO COLETA DO MÓDULO 3: CAPACITAÇÃO, BOLSAS E CURSOS ===")
    colecao = conectar_banco()
    total = 0
    total += raspar_estudar_fora(colecao)
    total += raspar_dio(colecao)
    total += adicionar_trilhas_ministerio_trabalho(colecao)
    logger.info(f"=== MÓDULO 3 CONCLUÍDO! Total de {total} registros atualizados. ===")
    return total


if __name__ == "__main__":
    raspar_todas_capacitacoes()
