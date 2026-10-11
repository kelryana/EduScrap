# backend/scraper_capacitacao_bolsas.py
"""
Scraper para Oportunidades de Capacitação, Certificações Gratuitas e Bolsas de Estudo.
Fontes integradas:
1. freeCodeCamp Brasil (tutoriais e trilhas gratuitas de programação em português, sem anúncios)
2. Alison.com (cursos online gratuitos com certificado/diploma em TI, gestão e dados)
3. Estudar Fora / Fundação Estudar (Bolsas internacionais de graduação, pós, STEM e mobilidade acadêmica)
4. Catálogo curado de plataformas gratuitas de cursos (Microsoft Learn, Coursera/Google, UFABC, USP, UFRJ etc.)

Observação: a fonte DIO.me foi removida do módulo por excesso de anúncios na plataforma,
e os cards "[MEC/MTE]" da Escola do Trabalhador 4.0 foram substituídos porque o site oficial
só oferece uma página geral (sem páginas individuais por curso).
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


def raspar_freecodecamp(colecao):
    """freeCodeCamp Brasil: tutoriais e trilhas gratuitas de programação (RSS oficial, sem anúncios)."""
    logger.info("-> Coletando capacitações do freeCodeCamp Brasil (feed RSS)...")
    url = "https://www.freecodecamp.org/portuguese/news/rss/"
    headers = {"User-Agent": "Mozilla/5.0"}
    total = 0

    try:
        resp = requests.get(url, headers=headers, timeout=12, verify=False)
        if resp.status_code != 200:
            logger.warning(f"Status {resp.status_code} ao acessar {url}")
            return 0

        soup = BeautifulSoup(resp.text, "xml")
        for it in soup.find_all("item")[:12]:
            titulo = it.title.get_text(strip=True) if it.title else ""
            link = it.link.get_text(strip=True) if it.link else ""
            desc_raw = it.description.get_text(strip=True) if it.description else ""
            snippet = BeautifulSoup(desc_raw, "html.parser").get_text(" ", strip=True)

            if not titulo or not link:
                continue

            classificacao = classificar_oportunidade(
                titulo, f"{snippet} Capacitação gratuita em programação, tecnologia e inteligência artificial"
            )
            cursos = classificacao["cursos"] or ["Ciência da Computação", "Engenharia de Software"]
            areas = ["Tecnologia", "Capacitação & Cursos"]

            documento = {
                "titulo": f"[freeCodeCamp] {titulo}",
                "nome": f"[freeCodeCamp] {titulo}",
                "descricao": (snippet[:400] if snippet else
                              f"Tutorial gratuito de programação e tecnologia do freeCodeCamp Brasil: {titulo}."),
                "link": link,
                "url": link,
                "fonte": "freeCodeCamp Brasil",
                "tipo": "capacitacao",
                "categoria": "Capacitação & Cursos",
                "status": "Aberto",
                "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
                "cursos": cursos,
                "areas": areas,
                "geral": False,
                "coletado_em": datetime.now().isoformat()
            }

            res = colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            if res.upserted_id or res.modified_count > 0:
                total += 1
                logger.info(f"   Salvo freeCodeCamp: {titulo[:50]}...")

    except Exception as e:
        logger.error(f"Erro ao coletar freeCodeCamp: {e}")

    return total


def raspar_alison(colecao):
    """Alison.com: plataforma internacional de cursos online gratuitos com certificado/diploma."""
    logger.info("-> Coletando cursos gratuitos com certificado da Alison.com...")
    categorias = [
        ("https://alison.com/courses/it", ["Ciência da Computação", "Sistemas de Informação", "Engenharia de Software"],
         ["Tecnologia", "Capacitação & Cursos"]),
        ("https://alison.com/courses/business", ["Administração", "Ciências Contábeis", "Economia"],
         ["Gestão", "Exatas", "Capacitação & Cursos"]),
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    total = 0
    vistos = set()

    for url, cursos_padrao, areas in categorias:
        try:
            resp = requests.get(url, headers=headers, timeout=12, verify=False)
            if resp.status_code != 200:
                logger.warning(f"Status {resp.status_code} ao acessar {url}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/course/" not in href or not href.startswith("http"):
                    continue

                titulo = a.get_text(" ", strip=True)
                # filtra links de texto corrido: títulos de curso são âncoras curtas e limpas
                if not titulo or len(titulo) < 8 or len(titulo) > 120 or titulo in vistos or href in vistos:
                    continue
                vistos.add(titulo)
                vistos.add(href)

                classificacao = classificar_oportunidade(titulo, "Curso online gratuito com certificado / diploma")
                cursos = classificacao["cursos"] or cursos_padrao

                documento = {
                    "titulo": f"[Alison] {titulo}",
                    "nome": f"[Alison] {titulo}",
                    "descricao": (f"Curso online gratuito da plataforma Alison com certificado/diploma reconhecido. "
                                  f"Cada curso leva direto à sua página individual de inscrição: {titulo}."),
                    "link": href,
                    "url": href,
                    "fonte": "Alison (Cursos Gratuitos com Certificado)",
                    "tipo": "capacitacao",
                    "categoria": "Capacitação & Cursos",
                    "status": "Aberto",
                    "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
                    "cursos": cursos,
                    "areas": areas,
                    "geral": False,
                    "coletado_em": datetime.now().isoformat()
                }

                res = colecao.update_one({"link": href}, {"$set": documento}, upsert=True)
                if res.upserted_id or res.modified_count > 0:
                    total += 1
                    logger.info(f"   Salvo Alison: {titulo[:50]}...")
                if total >= 12:
                    return total

        except Exception as e:
            logger.error(f"Erro ao coletar Alison ({url}): {e}")

    return total


def adicionar_catalogo_cursos_gratuitos(colecao):
    """Catálogo curado de cursos gratuitos com PÁGINA INDIVIDUAL (cada link abre o curso, não a home).
    Substitui os antigos cards [MEC/MTE] da Escola do Trabalhador 4.0, cujo site só possui página geral."""
    logger.info("-> Cadastrando catálogo curado de cursos gratuitos (páginas individuais)...")
    cursos = [
        {
            "titulo": "[Microsoft Learn] Fundamentos de Inteligência Artificial",
            "descricao": ("Módulo oficial e gratuito da Microsoft com trilha completa de IA generativa "
                          "(Azure AI). Página individual do módulo, sem anúncios."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-ai/",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Microsoft Learn] Noções básicas de análise de dados com Power BI",
            "descricao": ("Trilha oficial gratuita da Microsoft para análise de dados e Business Intelligence "
                          "com Power BI. Página individual do módulo."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-power-bi/",
            "cursos": ["Administração", "Ciências Contábeis", "Ciência da Computação", "Estatística"],
            "areas": ["Exatas", "Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Microsoft Learn] Noções básicas de computação em nuvem do Azure",
            "descricao": ("Fundamentos de Cloud Computing com Microsoft Azure, curso oficial gratuito "
                          "de nível de entrada. Página individual do módulo."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-azure-fundamentals/",
            "cursos": ["Ciência da Computação", "Sistemas de Informação", "Engenharia de Software"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Alison] Diploma em Programação Python",
            "descricao": ("Diploma online gratuito da Alison (com certificado reconhecido) cobrindo Python "
                          "do básico ao avançado. Página individual do curso."),
            "link": "https://alison.com/course/diploma-in-python-programming-revised",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Matemática"],
            "areas": ["Tecnologia", "Exatas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Alison] Elementos de Inteligência Artificial (IA)",
            "descricao": ("Curso gratuito da Alison sobre os fundamentos de IA e machine learning, "
                          "com certificado. Página individual do curso."),
            "link": "https://alison.com/course/elements-of-ai-artificial-intelligence",
            "cursos": ["Ciência da Computação", "Estatística", "Engenharia de Software"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Alison] Análise de Dados com Power BI",
            "descricao": ("Curso gratuito da Alison de Data Analytics usando Power BI, voltado à tomada "
                          "de decisão. Página individual do curso."),
            "link": "https://alison.com/course/data-analytics-using-power-bi",
            "cursos": ["Administração", "Estatística", "Ciências Contábeis"],
            "areas": ["Exatas", "Gestão", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Alison] Introdução ao Microsoft Azure",
            "descricao": ("Fundamentos de computação em nuvem com Azure na plataforma Alison, gratuito "
                          "e com certificado. Página individual do curso."),
            "link": "https://alison.com/course/introduction-to-microsoft-azure",
            "cursos": ["Ciência da Computação", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Coursera/Google] Certificado Profissional de Análise de Dados do Google",
            "descricao": ("Programa completo e gratuito (auditória) do Google no Coursera para se tornar "
                          "analista de dados, incluindo Power BI e SQL. Página individual do programa."),
            "link": "https://www.coursera.org/professional-certificates/google-data-analytics",
            "cursos": ["Estatística", "Ciência da Computação", "Administração"],
            "areas": ["Exatas", "Tecnologia", "Capacitação & Cursos"]
        },
    ]

    total = 0
    for t in cursos:
        doc = {
            "titulo": t["titulo"],
            "nome": t["titulo"],
            "descricao": t["descricao"],
            "link": t["link"],
            "url": t["link"],
            "fonte": "Catálogo Curado (Cursos Gratuitos)",
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
            logger.info(f"   Salvo catálogo: {t['titulo']}")

    return total


def limpar_fontes_antigas(colecao):
    """Remove registros obsoletos das fontes substituídas: DIO (excesso de anúncios)
    e Escola do Trabalhador 4.0 / MTE (links apenas para página geral, sem curso individual)."""
    removidos_dio = colecao.delete_many({
        "$or": [
            {"fonte": {"$regex": "Digital Innovation One|DIO", "$options": "i"}},
            {"titulo": {"$regex": "\\[DIO Tech\\]", "$options": "i"}},
            {"link": {"$regex": "dio\\.me", "$options": "i"}},
        ]
    }).deleted_count
    removidos_mte = colecao.delete_many({
        "$or": [
            {"titulo": {"$regex": "\\[MEC/MTE\\]", "$options": "i"}},
            {"link": {"$regex": "escoladotrabalhador40", "$options": "i"}},
        ]
    }).deleted_count
    if removidos_dio or removidos_mte:
        logger.info(f"   Limpeza: {removidos_dio} registros DIO e {removidos_mte} registros MEC/MTE removidos.")
    return removidos_dio + removidos_mte


def raspar_todas_capacitacoes():
    logger.info("=== INICIANDO COLETA DO MÓDULO 3: CAPACITAÇÃO, BOLSAS E CURSOS ===")
    colecao = conectar_banco()
    total = 0
    limpar_fontes_antigas(colecao)
    total += raspar_estudar_fora(colecao)
    total += raspar_freecodecamp(colecao)
    total += raspar_alison(colecao)
    total += adicionar_catalogo_cursos_gratuitos(colecao)
    logger.info(f"=== MÓDULO 3 CONCLUÍDO! Total de {total} registros atualizados. ===")
    return total


if __name__ == "__main__":
    raspar_todas_capacitacoes()
