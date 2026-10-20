# backend/scraper_capacitacao_bolsas.py

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
from base_scraper import configurar_log_scraper

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


def extrair_horas_e_preco_texto(texto: str):
    """
    Extrai carga horária (ex: '40 horas', '15h') e preço/investimento (ex: 'Gratuito', 'R$ 99,00')
    apenas se estiverem explicitamente mencionados no texto/snippet, sem fazer requisições extras.
    """
    if not texto:
        return None, None

    carga_horaria = None
    preco = None

    match_horas = re.search(
        r"\b(\d{1,4}\s*(?:horas?|hrs?|h))\b",
        texto,
        re.IGNORECASE,
    )
    if match_horas:
        valor_h = match_horas.group(1).strip()
        # Evita confundir horários como "14h" se não houver contexto de duração/carga/curso
        if re.search(r"horas?|hrs?|duraç|carga", valor_h + " " + texto, re.IGNORECASE):
            carga_horaria = valor_h

    match_preco = re.search(r"(R\$\s*\d+(?:[\.,]\d{2})?)", texto, re.IGNORECASE)
    if match_preco:
        preco = match_preco.group(1).strip()
    elif re.search(r"\b(100%\s*gratuit[oa]|totalmente\s*gratuit[oa]|curso\s*gratuit[oa]|bolsa\s*integral)\b", texto, re.IGNORECASE):
        preco = "Gratuito"

    return carga_horaria, preco


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

            carga_horaria, preco = extrair_horas_e_preco_texto(f"{titulo} {snippet}")

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
            if carga_horaria:
                documento["carga_horaria"] = carga_horaria
            if preco:
                documento["preco"] = preco

            res = colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            if res.upserted_id or res.modified_count > 0:
                total += 1
                logger.info(f"   Salvo Estudar Fora: {titulo[:50]}... | Cursos: {cursos}")

    except Exception as e:
        logger.error(f"Erro ao coletar Estudar Fora: {e}")

    return total


def raspar_freecodecamp(colecao):
    """freeCodeCamp Brasil: tutoriais e trilhas gratuitas de programação (RSS oficial, sem anúncios).
    Não realiza requisições extras caso o item (ex: episódio de podcast) não explicite horas/preço."""
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

            carga_horaria, preco = extrair_horas_e_preco_texto(f"{titulo} {snippet}")

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
            if carga_horaria:
                documento["carga_horaria"] = carga_horaria
            if preco:
                documento["preco"] = preco

            res = colecao.update_one({"link": link}, {"$set": documento}, upsert=True)
            if res.upserted_id or res.modified_count > 0:
                total += 1
                logger.info(f"   Salvo freeCodeCamp: {titulo[:50]}...")

    except Exception as e:
        logger.error(f"Erro ao coletar freeCodeCamp: {e}")

    return total


def adicionar_catalogo_cursos_gratuitos(colecao):
    """Catálogo curado de cursos gratuitos com PÁGINA INDIVIDUAL (cada link abre o curso, não a home),
    incluindo a carga horária e o preço/modalidade informados nas respectivas páginas."""
    logger.info("-> Cadastrando catálogo curado de cursos gratuitos (páginas individuais)...")
    cursos = [
        {
            "titulo": "[Microsoft Learn] Fundamentos de Inteligência Artificial",
            "descricao": ("Módulo oficial e gratuito da Microsoft com trilha completa de IA generativa "
                          "(Azure AI). Página individual do módulo, sem anúncios."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-ai/",
            "carga_horaria": "1 hora",
            "preco": "Gratuito",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Microsoft Learn] Noções básicas de análise de dados com Power BI",
            "descricao": ("Trilha oficial gratuita da Microsoft para análise de dados e Business Intelligence "
                          "com Power BI. Página individual do módulo."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-power-bi/",
            "carga_horaria": "1 hora",
            "preco": "Gratuito",
            "cursos": ["Administração", "Ciências Contábeis", "Ciência da Computação", "Estatística"],
            "areas": ["Exatas", "Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Microsoft Learn] Noções básicas de computação em nuvem do Azure",
            "descricao": ("Fundamentos de Cloud Computing com Microsoft Azure, curso oficial gratuito "
                          "de nível de entrada. Página individual do módulo."),
            "link": "https://learn.microsoft.com/pt-br/training/modules/get-started-with-azure-fundamentals/",
            "carga_horaria": "2 horas",
            "preco": "Gratuito",
            "cursos": ["Ciência da Computação", "Sistemas de Informação", "Engenharia de Software"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[freeCodeCamp] Certificação Cientista de Dados",
            "descricao": ("Trilha completa e gratuita do freeCodeCamp para Ciência de Dados "
                          "(Python, Pandas, visualização e machine learning), com certificação. "
                          "Página individual da certificação."),
            "link": "https://www.freecodecamp.org/portuguese/learn/data-analysis-with-python/",
            "carga_horaria": "300 horas",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Ciência da Computação", "Estatística", "Matemática"],
            "areas": ["Tecnologia", "Exatas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Kaggle Learn] Introdução ao Python",
            "descricao": ("Micro-curso gratuito e prático do Kaggle Learn para iniciantes em Python, "
                          "com notebooks interativos e certificado de conclusão. Página individual do curso."),
            "link": "https://www.kaggle.com/learn/python",
            "carga_horaria": "5 horas",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Ciência da Computação", "Estatística", "Engenharia de Software"],
            "areas": ["Tecnologia", "Exatas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[AWS Skill Builder] Fundamentos da AWS: Modelos de Nuvem",
            "descricao": ("Treinamento oficial gratuito da Amazon Web Services sobre fundamentos de "
                          "computação em nuvem, com certificado de conclusão. Página individual do curso."),
            "link": "https://explore.skillbuilder.aws/learn/course/internal/view/elearning/126/fundamentos-da-aws-modelos-de-nuvem",
            "carga_horaria": "1 hora",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Ciência da Computação", "Sistemas de Informação", "Engenharia de Software"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Coursera/Michigan] Como Aprender a Aprender",
            "descricao": ("Curso gratuito (modo auditório) mais popular do Coursera, da Universidade de "
                          "Michigan, sobre técnicas de aprendizagem eficazes. Página individual do curso."),
            "link": "https://www.coursera.org/learn/aprender",
            "carga_horaria": "15 horas",
            "preco": "Gratuito (modo auditório)",
            "cursos": ["Licenciatura", "Pedagogia", "Psicologia"],
            "areas": ["Humanas", "Educação", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Coursera/Google] Certificado Profissional de Análise de Dados do Google",
            "descricao": ("Programa completo e gratuito (auditória) do Google no Coursera para se tornar "
                          "analista de dados, incluindo Power BI e SQL. Página individual do programa."),
            "link": "https://www.coursera.org/professional-certificates/google-data-analytics",
            "carga_horaria": "180 horas",
            "preco": "Gratuito (modo auditório)",
            "cursos": ["Estatística", "Ciência da Computação", "Administração"],
            "areas": ["Exatas", "Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Fundação Bradesco] Microsoft Excel - Básico ao Avançado",
            "descricao": ("Curso 100% gratuito com certificado de conclusão emitido pela Escola Virtual da "
                          "Fundação Bradesco. Criação de planilhas, fórmulas e tabelas dinâmicas. Link individual."),
            "link": "https://www.ev.org.br/cursos/fundamentos-de-ti-e-produtividade/microsoft-excel-2016-basico",
            "carga_horaria": "15 horas",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Administração", "Ciências Contábeis", "Economia", "Engenharia de Produção"],
            "areas": ["Gestão", "Exatas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Fundação Bradesco] Linguagem de Programação Python",
            "descricao": ("Curso gratuito com certificado oficial da Fundação Bradesco para introdução à linguagem "
                          "Python, lógica de desenvolvimento e estruturas de dados. Link individual do curso."),
            "link": "https://www.ev.org.br/cursos/desenvolvimento-de-sistemas/linguagem-de-programacao-python-basico",
            "carga_horaria": "18 horas",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Capacitação & Cursos"]
        },
        {
            "titulo": "[FGV] Fundamentos da Gestão de Projetos",
            "descricao": ("Curso online gratuito da Fundação Getulio Vargas com declaração de conclusão. "
                          "Conceitos de escopo, prazos, custos e metodologias ágeis de projetos. Link individual."),
            "link": "https://educacao-executiva.fgv.br/cursos/online/curta-media-duracao-online/fundamentos-da-gestao-de-projetos",
            "carga_horaria": "5 horas",
            "preco": "Gratuito (com declaração)",
            "cursos": ["Administração", "Engenharia de Produção", "Gestão Pública"],
            "areas": ["Gestão", "Humanas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[FGV] Introdução à Ciência de Dados",
            "descricao": ("Curso gratuito da FGV sobre o papel da Ciência de Dados na tomada de decisão estratégica, "
                          "métricas analíticas e Big Data, com declaração de conclusão. Link individual."),
            "link": "https://educacao-executiva.fgv.br/cursos/online/curta-media-duracao-online/introducao-ciencia-de-dados",
            "carga_horaria": "60 horas",
            "preco": "Gratuito (com declaração)",
            "cursos": ["Ciência da Computação", "Estatística", "Administração"],
            "areas": ["Tecnologia", "Exatas", "Capacitação & Cursos"]
        },
        {
            "titulo": "[SEBRAE] Marketing Digital para o Empreendedor",
            "descricao": ("Capacitação oficial e gratuita do SEBRAE para posicionamento de marcas nas redes sociais, "
                          "análise de métricas e geração de leads. Link individual com certificado."),
            "link": "https://sebrae.com.br/sites/PortalSebrae/cursosonline/marketing-digital-para-o-empreendedor,b0d2b8a6a2862810VgnVCM100000d701210aRCRD",
            "carga_horaria": "2 horas",
            "preco": "Gratuito (com certificado)",
            "cursos": ["Administração", "Comunicação Social", "Publicidade"],
            "areas": ["Gestão", "Comunicação", "Capacitação & Cursos"]
        },
        {
            "titulo": "[Harvard CS50x / edX] Introdução à Ciência da Computação",
            "descricao": ("O famoso curso CS50 de Harvard oferecido gratuitamente pelo edX. C, Python, SQL, "
                          "algoritmos e desenvolvimento web com materiais didáticos de padrão internacional."),
            "link": "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-introduction-to-computer-science",
            "carga_horaria": "120 horas",
            "preco": "Gratuito",
            "cursos": ["Ciência da Computação", "Engenharia de Software", "Sistemas de Informação"],
            "areas": ["Tecnologia", "Exatas", "Capacitação & Cursos"]
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
            "carga_horaria": t.get("carga_horaria"),
            "preco": t.get("preco"),
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "cursos": t["cursos"],
            "areas": t["areas"],
            "geral": False,
            "coletado_em": datetime.now().isoformat()
        }
        colecao.update_one({"titulo": t["titulo"]}, {"$set": doc}, upsert=True)
        total += 1
        logger.info(f"   Salvo catálogo: {t['titulo']} ({t.get('carga_horaria')} - {t.get('preco')})")

    return total


def limpar_fontes_antigas(colecao):
    """Remove registros obsoletos das fontes substituídas."""
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
    removidos_alison = colecao.delete_many({
        "$or": [
            {"fonte": {"$regex": "alison", "$options": "i"}},
            {"titulo": {"$regex": "\\[Alison\\]", "$options": "i"}},
            {"link": {"$regex": "alison\\.com", "$options": "i"}},
        ]
    }).deleted_count
    if removidos_dio or removidos_mte or removidos_alison:
        logger.info(
            f"   Limpeza: {removidos_dio} registros DIO, {removidos_mte} registros MEC/MTE "
            f"e {removidos_alison} registros Alison removidos."
        )
    return removidos_dio + removidos_mte + removidos_alison


def raspar_todas_capacitacoes():
    logger.info("=== INICIANDO COLETA DO MÓDULO 3: CAPACITAÇÃO, BOLSAS E CURSOS ===")
    colecao = conectar_banco()
    total = 0
    limpar_fontes_antigas(colecao)
    total += raspar_estudar_fora(colecao)
    total += raspar_freecodecamp(colecao)
    total += adicionar_catalogo_cursos_gratuitos(colecao)
    logger.info(f"=== MÓDULO 3 CONCLUÍDO! Total de {total} registros atualizados. ===")
    return total


if __name__ == "__main__":
    configurar_log_scraper("capacitacao_bolsas", "Capacitação, freeCodeCamp e Bolsas de Estudo", "noticias", {"tipo": {"$in": ["capacitacao", "bolsa_estudo"]}})
    raspar_todas_capacitacoes()
