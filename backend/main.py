##backend/main.py
import logging
import os
import subprocess
import sys
import re
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BACKEND_DIR, "..", ".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("api.main")
from bson import ObjectId
from scraper_noticias import atualizar_noticias_agora
from api.auth import (
    hash_password,
    verify_password,
    generate_auth_token,
    decode_auth_token
)
from models import (
    OportunidadeModel,
    EditalModel,
    VagaEstagioModel,
    NoticiaModel,
    EstatisticasPrazos,
    UsuarioRegistroModel,
    UsuarioLoginModel,
    UsuarioRespostaModel
)
from mongo_database import MongoDatabase, get_mongo_database

app = FastAPI(
    title="API EduScrap",
    description="API RESTful oficial da plataforma EduScrap para agregação e consulta de oportunidades acadêmicas e editais.",
    version="1.3"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "")


def verificar_api_key(x_api_key: str = Header(default=None)):

    if not API_KEY:

        return True
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Acesso negado: informe o cabeçalho X-API-Key válido.",
        )
    return True

def verificar_admin(
    authorization: str = Header(default=None),
    x_api_key: str = Header(default=None)
):
    """
    Validação de credencial de administrador conforme RNF03 e UC12.
    Aceita chave administrativa X-API-Key ou token JWT de usuário com privilégio admin.
    """
    if x_api_key and (not API_KEY or x_api_key == API_KEY):
        return {"tipo": "api_key", "is_admin": True, "nome": "Admin (API Key)"}
    if authorization:
        try:
            usuario = obter_usuario_logado(authorization)
            if usuario.get("is_admin", False) or usuario.get("role") == "admin":
                return usuario
        except Exception:
            pass
    # Se não houver API_KEY configurada em dev, permite fallback informativo
    if not API_KEY and not authorization:
        return {"tipo": "dev_default", "is_admin": True, "nome": "Admin Local"}
    raise HTTPException(
        status_code=403,
        detail="Acesso restrito: credencial de Administrador requerida (UC12)."
    )


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

def obter_usuario_logado(authorization: str = Header(default=None)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autorização não fornecido")
    parts = authorization.split()
    token = parts[1] if len(parts) == 2 else parts[0]
    payload = decode_auth_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    try:
        user = db["usuarios"].find_one({"_id": ObjectId(payload["user_id"])})
    except Exception:
        user = db["usuarios"].find_one({"_id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    user["_id"] = str(user["_id"])
    user.pop("senha_hash", None)
    return user

def obter_usuario_opcional(authorization: str = Header(default=None)):

    if not authorization:
        return None
    try:
        parts = authorization.split()
        token = parts[1] if len(parts) == 2 else parts[0]
        payload = decode_auth_token(token)
        if not payload:
            return None
        try:
            user = db["usuarios"].find_one({"_id": ObjectId(payload["user_id"])})
        except Exception:
            user = db["usuarios"].find_one({"_id": payload["user_id"]})
        if not user:
            return None
        user["_id"] = str(user["_id"])
        user.pop("senha_hash", None)
        return user
    except Exception:
        return None
def garantir_metadados_fontes():
    try:
        colecao = db["fontes_provedores"]

        fontes_mestre = [
            {
                "_id": "prae_uern",
                "nome_oficial": "Pró-Reitoria de Assuntos Estudantis - UERN",
                "url_oficial": "https://prae.uern.br",
                "frequencia_monitoramento": "Diário",
                "foco_vagas": "Estágios Acadêmicos, Residência e Auxílios Financeiros"
            },
            {
                "_id": "proex_uern",
                "nome_oficial": "Pró-Reitoria de Extensão - UERN",
                "url_oficial": "https://proex.uern.br",
                "frequencia_monitoramento": "Diário",
                "foco_vagas": "Bolsas de Extensão, Cultura e Projetos de Pesquisa"
            },
            {
                "_id": "ufersa_oficial",
                "nome_oficial": "Portal de Editais - UFERSA",
                "url_oficial": "https://ufersa.edu.br",
                "frequencia_monitoramento": "A cada 12 hours",
                "foco_vagas": "Editais de Concursos, Estágios e Assistência Estudantil"
            },
            {
                "_id": "ciee_agente",
                "nome_oficial": "Centro de Integração Empresa-Escola (CIEE)",
                "url_oficial": "https://web.ciee.org.br",
                "frequencia_monitoramento": "A cada 6 hours",
                "foco_vagas": "Vagas de Estágio Comercial e Jovem Aprendiz Técnico"
            },
            {
                "_id": "portal_uern_oficial",
                "nome_oficial": "Portal UERN - Text Mining",
                "url_oficial": "https://portal.uern.br",
                "frequencia_monitoramento": "Diário",
                "foco_vagas": "Editais Internos Filtrados por Inteligência de Mineração"
            }
        ]

        for fonte in fontes_mestre:
            colecao.update_one({"_id": fonte["_id"]}, {"$set": fonte}, upsert=True)
    except Exception as e:
        logger.warning(f"Não foi possível sincronizar metadados das fontes no MongoDB: {e}")

garantir_metadados_fontes()


def resolver_vinculo_fonte(documento: dict):

    if not documento:
        return documento

    fonte_id = documento.get("fonte_id")
    if fonte_id:
        fonte_meta = db["fontes_provedores"].find_one({"_id": fonte_id})
        if fonte_meta:
            # Acopla dinamicamente os metadados ricos estruturados para consumo do front-end
            documento["meta_fonte"] = {
                "nome_oficial": fonte_meta.get("nome_oficial"),
                "url_oficial": fonte_meta.get("url_oficial"),
                "frequencia": fonte_meta.get("frequencia_monitoramento")
            }
    return documento

def enriquecer_prazo(documento: dict):
    """
    Calcula o status do prazo de inscrição comparando data_vencimento com a data atual.
    Adiciona: data_vencimento_formatada, status_prazo ('vigente' | 'vencido' | 'sem_prazo')
    e dias_restantes (negativo quando já venceu).
    """
    if not documento:
        return documento

    vencimento = documento.get("data_vencimento")

    # Para notícias tecnológicas, não aplicamos o conceito de prazo
    categoria = documento.get("categoria", "")
    fonte = documento.get("fonte", "")
    fonte_id = documento.get("fonte_id", "")

    # Verifica se é conteúdo de notícia técnica que não tem prazo por natureza
    if ("notícia tech" in categoria.lower() or
        "g1" in fonte.lower() or
        "canaltech" in fonte.lower() or
        "noticias" in fonte_id.lower() or
        "ciee_agente" == fonte_id):  # CIEE entries don't have deadlines either
        # Não adiciona informações de prazo para este tipo de conteúdo
        documento["status_prazo"] = "sem_prazo_aplicavel"  # Indica que o tipo de conteúdo não tem prazo
        return documento

    if isinstance(vencimento, datetime):
        documento["data_vencimento_formatada"] = vencimento.strftime("%d/%m/%Y")
        dias = (vencimento.date() - datetime.now().date()).days
        documento["dias_restantes"] = dias
        documento["status_prazo"] = "vigente" if dias >= 0 else "vencido"
    else:
        documento["status_prazo"] = "sem_prazo"
    return documento

def extrair_e_converter_data(texto: str) -> datetime:
    if not texto:
        return None
    padrao_data = r"\b(\d{2})/(\d{2})/(\d{4})\b"
    resultado = re.search(padrao_data, texto)
    if resultado:
        dia, mes, ano = resultado.groups()
        try:
            return datetime(int(ano), int(mes), int(dia))
        except ValueError:
            return None
    return None


def enriquecer_doc(documento: dict, usuario: dict = None):
    if not documento:
        return documento
    documento = enriquecer_prazo(documento)
    documento = resolver_vinculo_fonte(documento)
    if usuario and "favoritos" in usuario:
        fav_set = set(usuario.get("favoritos", []))
        documento["favorito"] = str(documento.get("_id")) in fav_set
    else:
        documento["favorito"] = False
    return documento


# Rota de teste
@app.get("/")
def raiz():
    return {
        "mensagem": "A API do EduScrap está online! Acesse /docs para testar.",
        "versao": "1.3",
        "docs": "/docs"
    }

@app.get("/api/oportunidades")
def listar_todas_oportunidades(
    categoria: str = Query(None, description="Filtro por categoria (ex: estagio, bolsa, edital, noticia)"),
    fonte: str = Query(None, description="Filtro por fonte oficial (ex: PRAE, PROEX, UFERSA, CIEE)"),
    busca: str = Query(None, description="Termo para busca textual por palavra-chave"),
    apenas_vigentes: bool = Query(False, description="Filtrar apenas certames com inscrições vigentes"),
    pagina: int = Query(1, ge=1),
    limite: int = Query(10, ge=1, le=100),
    authorization: str = Header(default=None)
):
    """
    UC01, UC02, UC03, UC04 & Figura 4:
    Consulta unificada e consolidada de oportunidades com ordenação temporal, busca e filtros.
    """
    usuario = obter_usuario_opcional(authorization)
    todas_colecoes = [
        "vagas_estagio", "vagas_bolsa", "vagas_ufersa",
        "vagas_ciee", "vagas_portal_uern", "editais", "vagas",
        "noticias", "vagas_noticias", "oportunidades"
    ]
    nomes_existentes = set(db.list_collection_names())
    colecoes_para_buscar = [c for c in todas_colecoes if c in nomes_existentes]

    # Mapeamento opcional de categoria para coleções específicas
    mapa_categorias = {
        "estagio": ["vagas_estagio", "vagas_ciee", "vagas"],
        "estagios": ["vagas_estagio", "vagas_ciee", "vagas"],
        "bolsa": ["vagas_bolsa", "vagas_ufersa"],
        "bolsas": ["vagas_bolsa", "vagas_ufersa"],
        "edital": ["editais", "vagas_ufersa", "vagas_bolsa"],
        "editais": ["editais", "vagas_ufersa", "vagas_bolsa"],
        "noticia": ["noticias", "vagas_noticias"],
        "noticias": ["noticias", "vagas_noticias"]
    }
    if categoria and categoria.lower() in mapa_categorias:
        colecoes_para_buscar = [c for c in mapa_categorias[categoria.lower()] if c in nomes_existentes]

    filtro_base = {}
    if fonte:
        filtro_base["fonte"] = {"$regex": re.escape(fonte), "$options": "i"}
    if apenas_vigentes:
        filtro_base["data_vencimento"] = {"$gte": datetime.now()}

    documentos = []
    links_vistos = set()

    for col_name in colecoes_para_buscar:
        try:
            col = db[col_name]
            f = dict(filtro_base)
            if busca:
                f["$or"] = [
                    {"nome": {"$regex": re.escape(busca), "$options": "i"}},
                    {"titulo": {"$regex": re.escape(busca), "$options": "i"}},
                    {"descricao": {"$regex": re.escape(busca), "$options": "i"}},
                    {"tags": {"$regex": re.escape(busca), "$options": "i"}}
                ]

            for doc in col.find(f).limit(limite * 5):
                link = doc.get("link")
                if link and link in links_vistos:
                    continue
                if link:
                    links_vistos.add(link)

                doc["_id"] = str(doc["_id"])
                # Normaliza titulo/nome
                if "titulo" not in doc and "nome" in doc:
                    doc["titulo"] = doc["nome"]
                doc = enriquecer_doc(doc, usuario)

                if apenas_vigentes and doc.get("status_prazo") == "vencido":
                    continue

                documentos.append(doc)
        except Exception as e:
            logger.warning(f"Erro ao consultar coleção {col_name}: {e}")

    # Ordenação: vigentes com prazo mais próximo primeiro, depois sem prazo, depois vencidos
    def ordenar_chave(d):
        v = d.get("data_vencimento")
        if isinstance(v, datetime):
            return (0 if v >= datetime.now() else 2, v)
        return (1, datetime.max)

    documentos.sort(key=ordenar_chave)
    total = len(documentos)
    inicio = (pagina - 1) * limite
    fim = inicio + limite
    itens_paginados = documentos[inicio:fim]

    return {
        "sucesso": True,
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total,
        "dados": itens_paginados
    }


@app.get("/api/estagios")
def listar_estagios(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas_estagio"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_vagas = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        vaga = enriquecer_doc(vaga, usuario)
        lista_vagas.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_vagas
    }

@app.get("/api/bolsas")
def listar_bolsas(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas_bolsa"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_bolsas = []
    for bolsa in colecao.find(filtro).skip(pulo).limit(limite):
        bolsa["_id"] = str(bolsa["_id"])
        bolsa = enriquecer_doc(bolsa, usuario)
        lista_bolsas.append(bolsa)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_bolsas
    }

@app.get("/api/ufersa")
def listar_ufersa(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    docs_ufersa = []
    # 1. CPPS da UFERSA
    for ed in db["editais"].find({"fonte": {"$regex": "UFERSA", "$options": "i"}}):
        docs_ufersa.append(ed)
    # 2. PROAE da UFERSA
    for vg in db["vagas_ufersa"].find(filtro):
        docs_ufersa.append(vg)

    total_docs = len(docs_ufersa)
    docs_paginados = docs_ufersa[pulo : pulo + limite]

    lista_ufersa = []
    for edital in docs_paginados:
        edital["_id"] = str(edital["_id"])
        edital = enriquecer_doc(edital, usuario)
        lista_ufersa.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total_docs,
        "dados": lista_ufersa
    }
@app.get("/api/ciee")
def listar_ciee(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas_ciee"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_ciee = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        vaga["nome"] = vaga.get("nome_completo") or vaga.get("titulo") or "Vaga CIEE"
        vaga["titulo"] = vaga["nome"]
        vaga = enriquecer_doc(vaga, usuario)
        lista_ciee.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_ciee
    }

@app.get("/api/mprn")
def listar_mprn(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas"]
    pulo = (pagina - 1) * limite

    filtro = {"fonte": {"$regex": "MPRN", "$options": "i"}}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    total_docs = colecao.count_documents(filtro)
    lista_mprn = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        vaga["nome"] = vaga.get("titulo") or vaga.get("nome") or "Seleção MPRN"
        vaga["titulo"] = vaga["nome"]
        vaga = enriquecer_doc(vaga, usuario)
        lista_mprn.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total_docs,
        "dados": lista_mprn
    }

@app.get("/api/ifrn")
def listar_ifrn(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["editais"]
    pulo = (pagina - 1) * limite

    filtro = {"fonte": {"$regex": "IFRN", "$options": "i"}}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}
    total_docs = colecao.count_documents(filtro)
    lista_ifrn = []
    for edital in colecao.find(filtro).skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        edital["nome"] = edital.get("titulo") or edital.get("nome") or "Processo IFRN"
        edital["titulo"] = edital["nome"]
        edital = enriquecer_doc(edital, usuario)
        lista_ifrn.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total_docs,
        "dados": lista_ifrn
    }

@app.get("/api/iel")
def listar_iel(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas"]
    pulo = (pagina - 1) * limite

    filtro = {"fonte": {"$regex": "IEL", "$options": "i"}}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}
    total_docs = colecao.count_documents(filtro)
    lista_iel = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        vaga["nome"] = vaga.get("titulo") or vaga.get("nome") or "Vaga IEL/RN"
        vaga["titulo"] = vaga["nome"]
        vaga = enriquecer_doc(vaga, usuario)
        lista_iel.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total_docs,
        "dados": lista_iel
    }

@app.get("/api/dom")
def listar_dom(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["editais"]
    pulo = (pagina - 1) * limite

    filtro = {
        "$or": [
            {"fonte": {"$regex": "Prefeitura de Mossoró", "$options": "i"}},
            {"titulo": {"$regex": r"\[DOM/Mossoró\]", "$options": "i"}}
        ]
    }
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}
    total_docs = colecao.count_documents(filtro)
    lista_dom = []
    for edital in colecao.find(filtro).skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        edital["nome"] = edital.get("titulo") or edital.get("nome") or "Edital Municipal"
        edital["titulo"] = edital["nome"]
        edital = enriquecer_doc(edital, usuario)
        lista_dom.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": total_docs,
        "dados": lista_dom
    }

@app.get("/api/portal_uern")
def listar_portal_uern(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas_portal_uern"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_portal = []
    for edital in colecao.find(filtro).skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        edital = enriquecer_doc(edital, usuario)
        lista_portal.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_portal
    }


# Marcadores de conteúdo de capacitação/cursos gravados na coleção "noticias"
# pelo scraper_capacitacao_bolsas (aba Cursos & Bolsas). Não são notícias reais.
MARCADORES_CAPACITACAO = [
    "capacitação", "capacitacao",
    "cursos gratuitos", "bolsas de estudo",
    "freecodecamp", "microsoft learn",
    "coursera", "fundação estudar", "fundacao estudar",
]


def eh_documento_de_noticia(doc: dict) -> bool:
    """Identifica se um documento da coleção 'noticias' é uma notícia real
    (ex.: ASSECOM UFERSA), e não um card de capacitação/cursos/bolsas."""
    tipo = (doc.get("tipo") or "").lower()
    categoria = (doc.get("categoria") or "").lower()
    texto = f"{doc.get('titulo', '')} {doc.get('nome', '')} {doc.get('descricao', '')}".lower()

    eh_capacitacao = (
        tipo in ("capacitacao", "bolsa_estudo")
        or any(marcador in categoria for marcador in MARCADORES_CAPACITACAO)
        or any(marcador in texto for marcador in MARCADORES_CAPACITACAO)
    )
    return not eh_capacitacao


def paginar_docs(lista_docs, pagina: int, limite: int, usuario: dict):
    pulo = (pagina - 1) * limite
    docs_paginados = lista_docs[pulo : pulo + limite]
    lista = []
    for doc in docs_paginados:
        doc["_id"] = str(doc["_id"])
        doc = enriquecer_doc(doc, usuario)
        lista.append(doc)
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": len(lista_docs),
        "dados": lista
    }


@app.get("/api/cursos-bolsas")
def listar_cursos_bolsas(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    """Aba 'Cursos & Bolsas': bootcamps, cursos gratuitos com certificado e
    bolsas de estudo (freeCodeCamp, Microsoft Learn, Estudar Fora...).
    Antes esta rota não existia na API, causando o erro 404 no front-end."""
    usuario = obter_usuario_opcional(authorization)
    pulo = (pagina - 1) * limite

    filtro = {"tipo": {"$in": ["capacitacao", "bolsa_estudo"]}}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    docs_curso = list(db["noticias"].find(filtro).sort("coletado_em", -1))

    # Remove notícias institucionais e links genéricos de páginas gerais (como Alison)
    docs_curso = [
        d for d in docs_curso
        if (d.get("tipo") or "") != "noticia"
        and "alison.com" not in (d.get("link") or "").lower()
        and "[alison]" not in (d.get("titulo") or "").lower()
    ]

    return paginar_docs(docs_curso, pagina, limite, usuario)


@app.get("/api/noticias-ufersa")
def listar_noticias_ufersa(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    """Aba 'Notícias UFERSA': notícias institucionais do portal ASSECOM UFERSA
    (ex.: 'Estudantes fazem visita técnica ao Projeto Malha d'Água e ao açude Cedro').
    Antes esta rota não existia na API e caía no endpoint de editais, exibindo
    tags erradas ('Editais UFERSA') e o erro 404."""
    usuario = obter_usuario_opcional(authorization)

    filtro_base = {
        "$or": [
            {"fonte": {"$regex": "UFERSA", "$options": "i"}},
            {"titulo": {"$regex": "ufersa", "$options": "i"}},
        ]
    }
    filtro_noticias = dict(filtro_base)
    filtro_noticias["tipo"] = "noticia"
    if apenas_vigentes:
        filtro_noticias["data_vencimento"] = {"$gte": datetime.now()}

    docs_noticias = []
    for col_name in ("noticias", "vagas_noticias"):
        try:
            for doc in db[col_name].find(filtro_noticias).sort("coletado_em", -1):
                doc["nome"] = doc.get("titulo") or doc.get("nome") or "Notícia UFERSA"
                doc["titulo"] = doc["nome"]
                if not doc.get("categoria"):
                    doc["categoria"] = "Notícia UFERSA"
                docs_noticias.append(doc)
        except Exception as e:
            logger.warning(f"Falha ao buscar notícias UFERSA na coleção {col_name}: {e}")

    return paginar_docs(docs_noticias, pagina, limite, usuario)


@app.get("/api/noticias")
def listar_noticias(
    pagina: int = Query(1, ge=1),
    limite: int = Query(6, ge=1),
    apenas_vigentes: bool = False,
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao_cache = db["controle_cache"]
    ultimo_registro = colecao_cache.find_one({"tipo": "noticias"})

    tempo_limite = datetime.now() - timedelta(minutes=10)

    if not ultimo_registro or ultimo_registro["data_execucao"] < tempo_limite:
        logger.info("[CACHE] Cache expirado ou inexistente. Acionando robô de notícias...")
        atualizar_noticias_agora()

        colecao_cache.update_one(
            {"tipo": "noticias"},
            {"$set": {"data_execucao": datetime.now()}},
            upsert=True
        )
    else:
        logger.info("[CACHE] Dados recuperados localmente via cache ativo do MongoDB.")

    pulo = (pagina - 1) * limite
    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    docs_todos = []

    def eh_noticia_ufersa(doc: dict) -> bool:
        """Notícias institucionais da UFERSA pertencem EXCLUSIVAMENTE à aba
        'Notícias UFERSA' (/api/noticias-ufersa), nunca à aba geral de Notícias."""
        texto = f"{doc.get('fonte', '')} {doc.get('titulo', '') or doc.get('nome', '')}".lower()
        return "ufersa" in texto

    # 1. Notícias reais da coleção "noticias" (portais acadêmicos etc.).
    #    Cards de capacitação/cursos/bolsas ficam EXCLUSIVAMENTE na aba Cursos & Bolsas,
    #    e notícias da UFERSA ficam EXCLUSIVAMENTE na aba Notícias UFERSA.
    for doc in db["noticias"].find(filtro).sort("coletado_em", -1):
        if not eh_documento_de_noticia(doc):
            continue
        if eh_noticia_ufersa(doc):
            continue
        doc["nome"] = doc.get("titulo") or doc.get("nome") or "Notícia"
        doc["titulo"] = doc["nome"]
        if not doc.get("categoria"):
            doc["categoria"] = "Notícia"
        docs_todos.append(doc)

    # 2. Notícias gerais ao vivo (G1 Educação/Saúde, Agência Brasil, Tech...) —
    #    exclui qualquer documento com marca de UFERSA.
    for doc in db["vagas_noticias"].find(filtro):
        if eh_noticia_ufersa(doc):
            continue
        doc["titulo"] = doc.get("nome") or doc.get("titulo") or "Notícia"
        if not doc.get("categoria"):
            doc["categoria"] = "Notícia"
        docs_todos.append(doc)

    return paginar_docs(docs_todos, pagina, limite, usuario)

@app.get("/api/pesquisar")
def pesquisar_unificado(
    termo: str = Query(..., min_length=2),
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_portal_uern"]
    resultados = []
    for col_name in db.list_collection_names():
        if col_name in colecoes:
            try:
                cursor = db[col_name].find({"$text": {"$search": termo}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    doc = enriquecer_doc(doc, usuario)
                    resultados.append(doc)
            except Exception:
                cursor = db[col_name].find({"nome": {"$regex": termo, "$options": "i"}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    doc = enriquecer_doc(doc, usuario)
                    resultados.append(doc)
    return resultados

@app.get("/api/estatisticas")
def obter_estatisticas():
    nome_colecoes = db.list_collection_names()

    # Notícias reais (exclui cards de capacitação/cursos/bolsas da aba Cursos & Bolsas)
    noticias_reais = [d for d in db["noticias"].find({}) if eh_documento_de_noticia(d)]
    total_noticias_ufersa = sum(
        1 for d in noticias_reais if "ufersa" in (d.get("fonte") or "").lower()
    ) + db["vagas_noticias"].count_documents({"tipo": "noticia"})

    totais = {
        "estagios": db["vagas_estagio"].count_documents({}),
        "bolsas": db["vagas_bolsa"].count_documents({}),
        "ufersa": db["vagas_ufersa"].count_documents({}),
        "ciee": db["vagas_ciee"].count_documents({}),
        "noticias": db["vagas_noticias"].count_documents({}) + len(noticias_reais),
        "noticias_ufersa": total_noticias_ufersa,
        "cursos_bolsas": db["noticias"].count_documents({"tipo": {"$in": ["capacitacao", "bolsa_estudo"]}}),
        "portal_uern": db["vagas_portal_uern"].count_documents({}),
    }

    # ---- Fontes que NÃO têm coleção dedicada ----
    # Os scrapers de MPRN e IEL gravam na coleção "vagas"; IFRN e DOM Mossoró
    # gravam na coleção "editais". As contagens por fonte são feitas pelo campo
    # "fonte", espelhando exatamente os filtros dos endpoints /api/mprn, /api/iel,
    # /api/ifrn e /api/dom. Assim o KPI "DOM Mossoró" (e MPRN/IEL/IFRN) deixa de
    # retornar 0 por consultar coleções fantasmas ("vagas_mprn", "vagas_dom"...).
    def _contar_por_fonte(colecao_nome, regex_fonte):
        try:
            return db[colecao_nome].count_documents(
                {"fonte": {"$regex": regex_fonte, "$options": "i"}}
            )
        except Exception:
            return 0

    extras_fonte = {
        "mprn": _contar_por_fonte("vagas", r"MPRN|Ministério Público"),
        "iel": _contar_por_fonte("vagas", r"IEL"),
        "ifrn": _contar_por_fonte("editais", r"IFRN"),
        "dom": _contar_por_fonte("editais", r"Prefeitura de Mossoró|DOM/Mossoró"),
    }
    # Soma (não substitui): se um dia existirem coleções dedicadas além dos
    # documentos compartilhados, nenhuma captação é perdida.
    for chave, valor in extras_fonte.items():
        totais[chave] = (totais.get(chave) or 0) + valor

    total_geral = sum(totais.values())

    agora = datetime.now()
    janela_limite = agora + timedelta(days=7)

    query_reta_final = {
        "data_vencimento": {
            "$gte": agora,
            "$lte": janela_limite
        }
    }

    colecoes_prazo = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_mprn", "vagas_ifrn", "vagas_iel", "vagas_dom"]

    # Documentos compartilhados nas coleções genéricas "vagas" e "editais"
    # (MPRN, IEL, IFRN, DOM Mossoró...) também têm prazo de inscrição e devem
    # entrar na conta de reta final / saúde do hub. Filtro espelha os endpoints
    # /api/mprn, /api/iel, /api/ifrn e /api/dom.
    filtro_fontes_compartilhadas = {
        "$or": [
            {"fonte": {"$regex": r"MPRN|Ministério Público|IEL|IFRN|Prefeitura de Mossoró|DOM/Mossoró", "$options": "i"}},
            {"titulo": {"$regex": r"\[DOM/Mossoró\]|\[MPRN\]|\[IEL", "$options": "i"}},
        ]
    }
    def _consulta_prazo(colecao_nome, base_query):
        q = dict(base_query)
        q["$and"] = [filtro_fontes_compartilhadas]
        return q

    total_reta_final = sum(db[col].count_documents(query_reta_final) for col in colecoes_prazo if col in nome_colecoes)
    query_vigentes = {"data_vencimento": {"$gte": agora}}
    total_oportunidades_com_prazo = sum(
        db[col].count_documents({}) for col in colecoes_prazo if col in nome_colecoes
    )
    total_vigentes = sum(
        db[col].count_documents(query_vigentes) for col in colecoes_prazo if col in nome_colecoes
    )
    # Editais VENCIDOS (prazo de inscrição já encerrado) — alimenta o card
    # "Editais: Abertos x Vencidos" do dashboard.
    query_vencidos = {"data_vencimento": {"$lt": agora}}
    total_vencidos = sum(
        db[col].count_documents(query_vencidos) for col in colecoes_prazo if col in nome_colecoes
    )
    for col_extra in ["vagas", "editais"]:
        if col_extra not in nome_colecoes:
            continue
        try:
            total_reta_final += db[col_extra].count_documents(_consulta_prazo(col_extra, query_reta_final))
            total_extra = db[col_extra].count_documents(_consulta_prazo(col_extra, {}))
            total_oportunidades_com_prazo += total_extra
            total_vigentes += db[col_extra].count_documents(_consulta_prazo(col_extra, query_vigentes))
            total_vencidos += db[col_extra].count_documents(_consulta_prazo(col_extra, query_vencidos))
        except Exception:
            continue

    def _titulo_documento(doc):
        return (doc.get("titulo") or doc.get("nome") or "Sem título").strip()

    def _coletar_lista(query, colecoes, limite, ordena_asc=True):
        """Puxa uma amostra real de editais para o painel de prazos."""
        itens = []
        projection = {"titulo": 1, "nome": 1, "data_vencimento": 1, "link": 1, "url": 1, "link_edital": 1}
        for col in colecoes:
            if col not in nome_colecoes or len(itens) >= limite:
                continue
            try:
                filtro_busca = _consulta_prazo(col, query) if col in ["vagas", "editais"] else query
                cursor = db[col].find(filtro_busca, projection).sort(
                    "data_vencimento", 1 if ordena_asc else -1
                ).limit(limite - len(itens))
                for doc in cursor:
                    venc = doc.get("data_vencimento")
                    if isinstance(venc, datetime):
                        itens.append({
                            "id": str(doc.get("_id", "")),
                            "titulo": _titulo_documento(doc),
                            "data": venc.strftime("%d/%m/%Y"),
                            "data_iso": venc.isoformat(),
                            "link": (doc.get("link") or doc.get("url") or doc.get("link_edital") or ""),
                        })
            except Exception:
                continue
        itens.sort(key=lambda item: datetime.strptime(item["data"], "%d/%m/%Y"), reverse=not ordena_asc)
        return itens[:limite]

    editais_abertos = _coletar_lista(query_vigentes, colecoes_prazo + ["vagas", "editais"], 20, ordena_asc=True)
    proximos_a_vencer = _coletar_lista(query_reta_final, colecoes_prazo + ["vagas", "editais"], 10, ordena_asc=True)
    vencidos_recentes = _coletar_lista(query_vencidos, colecoes_prazo + ["vagas", "editais"], 15, ordena_asc=False)

    # ---- Distribuição por CATEGORIA em TODO o hub (não apenas PRAE) ----
    # Antes este bloco agrupava somente a coleção "vagas_estagio" (estágios PRAE).
    # Agora varre todas as coleções de oportunidades/notícias do hub, agregando
    # pelo campo "categoria" e somando as contagens entre coleções.
    pipeline_categoria = [
        {"$match": {"categoria": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {"_id": "$categoria", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    contagem_categorias = {}
    for col in nome_colecoes:
        if col in ("controle_cache", "historico_varreduras", "fontes_provedores", "usuarios"):
            continue
        try:
            for item in db[col].aggregate(pipeline_categoria):
                chave = item["_id"] or "Geral / Não Especificada"
                contagem_categorias[chave] = contagem_categorias.get(chave, 0) + item["total"]
        except Exception:
            continue
    distribuicao_categorias = sorted(
        [{"categoria": chave, "total": total} for chave, total in contagem_categorias.items()],
        key=lambda item: item["total"],
        reverse=True
    )
    formatar = lambda lista: [{"categoria": item["categoria"], "total": item["total"]} for item in lista]

    # ---- Fluxo REAL de captação dos últimos 7 dias (por dia da semana) ----
    # Usa o campo de data mais confiável disponível em cada coleção.
    inicio_janela = (agora - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    campos_data_captura = ["criado_em", "data_publicacao", "data_criacao", "coletado_em", "updated_at", "data_noticia"]
    nomes_dias = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
    contagem_por_dia = [0] * 7

    def _normalizar_dt(valor):
        """Aceita datetime ISO, string 'YYYY-MM-DD' (formato usado pelos
        scrapers de DOM/Mossoró, MPRN, IEL e IFRN), string ISO com hora ou date."""
        if isinstance(valor, datetime):
            return valor
        if isinstance(valor, str):
            texto = valor.strip().replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(texto)
            except ValueError:
                pass
            try:
                return datetime.strptime(texto[:10], "%Y-%m-%d")
            except ValueError:
                return None
        # datetime.date puro (sem hora)
        try:
            import datetime as _dtmod
            if isinstance(valor, _dtmod.date):
                return datetime(valor.year, valor.month, valor.day)
        except Exception:
            return None
        return None

    def _extrair_dt_documento(doc):
        for campo in campos_data_captura:
            dt = _normalizar_dt(doc.get(campo))
            if dt:
                return dt
        return None

    # Varre TODAS as coleções do hub — inclusive as genéricas "vagas" e
    # "editais", onde vivem MPRN, IEL, IFRN e DOM Mossoró. Assim o fluxo
    # semanal passa a contabilizar essas fontes também.
    for col in nome_colecoes:
        try:
            cursor = db[col].find({}, projection={c: 1 for c in campos_data_captura})
            for doc in cursor:
                dt = _extrair_dt_documento(doc)
                if dt and inicio_janela <= dt <= agora + timedelta(days=1):
                    contagem_por_dia[dt.weekday()] += 1
        except Exception:
            continue

    cores_dias = ["#10B981", "#FF5C00", "#0F172A", "#38BDF8", "#8B5CF6", "#FACC15", "#FB923C"]
    ordem_exibicao = [6, 0, 1, 2, 3, 4, 5]  # DOM, SEG..SÁB
    tem_dados_fluxo = any(contagem_por_dia)
    dias_semana = []
    for idx in ordem_exibicao:
        dias_semana.append({
            "dia": nomes_dias[idx],
            "valor": contagem_por_dia[idx] if tem_dados_fluxo else 0,
            "cor": cores_dias[idx]
        })

    # ---- Status da última varredura automatizada ----
    ultima_varredura = None
    if "historico_varreduras" in nome_colecoes:
        try:
            log = db["historico_varreduras"].find_one(
                {}, sort=[("data_execucao", -1)]
            )
            if log:
                data_exec = log.get("data_execucao")
                ultima_varredura = {
                    "data": data_exec.isoformat() if isinstance(data_exec, datetime) else None,
                    "status": log.get("status"),
                    "duracao_segundos": log.get("tempo_duracao_segundos"),
                }
        except Exception:
            ultima_varredura = None

    # ---- Ranking real das origens monitoradas (para o radar de fontes) ----
    ranking_fontes = sorted(
        [{"origem": chave, "total": valor} for chave, valor in totais.items() if valor > 0],
        key=lambda item: item["total"],
        reverse=True
    )

    canais_monitorados = sum(1 for v in totais.values() if v and v > 0)

    return {
        "totais": totais,
        "total_geral": total_geral,
        "reta_final_urgente": total_reta_final,
        "vigentes": total_vigentes,
        "vencidos": total_vencidos,
        "editais_abertos": editais_abertos,
        "proximos_a_vencer": proximos_a_vencer,
        "vencidos_recentes": vencidos_recentes,
        "oportunidades_com_prazo": total_oportunidades_com_prazo,
        # Distribuição por categoria de TODO o hub (todas as fontes/coleções).
        # Mantém a chave legada "prae_categorias" para compatibilidade com
        # clientes antigos; a nova chave canônica é "categorias_hub".
        "categorias_hub": formatar(distribuicao_categorias),
        "prae_categorias": formatar(distribuicao_categorias),
        "fluxo_semanal": dias_semana,
        "tem_dados_fluxo": tem_dados_fluxo,
        "ultima_varredura": ultima_varredura,
        "ranking_fontes": ranking_fontes,
        "canais_monitorados": canais_monitorados
    }
@app.get("/api/db-status")
def obter_status_do_banco():
    status_colecoes = []
    # Adicionado vagas_portal_uern para auditoria transparente
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_noticias", "vagas_portal_uern", "historico_varreduras", "fontes_provedores"]

    for col_name in colecoes:
        colecao = db[col_name]
        try:
            indices_brutos = list(colecao.list_indexes())
            indices_nomes = [idx["name"] for idx in indices_brutos]
        except Exception:
            indices_nomes = ["_id_"]

        try:
            stats = db.command("collStats", col_name)
            tamanho_kb = round(stats.get("size", 0) / 1024, 2)
            documentos_qtd = stats.get("count", 0)
        except Exception:
            tamanho_kb = 0.0
            documentos_qtd = colecao.count_documents({})

        has_validator = False
        try:
            col_info = db.command("listCollections", filter={"name": col_name})["cursor"]["firstBatch"]
            if col_info and "options" in col_info[0] and "validator" in col_info[0]["options"]:
                has_validator = True
        except Exception:
            pass

        status_colecoes.append({
            "colecao": col_name,
            "documentos": documentos_qtd,
            "tamanho_kb": tamanho_kb,
            "indices": indices_nomes,
            "has_validator": has_validator
        })

    return {
        "banco": "hub_estudantes",
        "host": "MongoDB Local (localhost:27017)",
        "colecoes": status_colecoes
    }


# ==========================================
# ROTAS DE AUTENTICAÇÃO E PERFIL DO ALUNO
# ==========================================

@app.get("/api/auth/verificar-email")
def verificar_email_disponivel(email: str = Query(..., description="E-mail para consulta")):
    """Verifica se o e-mail informado já está cadastrado no sistema."""
    email_limpo = email.strip().lower()
    if not email_limpo or "@" not in email_limpo or "." not in email_limpo.split("@")[-1]:
        return {
            "valido": False,
            "existe": False,
            "mensagem": "Formato de e-mail inválido."
        }
    
    usuario_existente = db["usuarios"].find_one({"email": email_limpo})
    if usuario_existente:
        return {
            "valido": True,
            "existe": True,
            "mensagem": "Este e-mail já está cadastrado no EduScrap. Faça login ou redefina sua senha."
        }
    return {
        "valido": True,
        "existe": False,
        "mensagem": "E-mail disponível para cadastro!"
    }


@app.post("/api/auth/register")
def register_usuario(payload: dict):
    nome = payload.get("nome", "").strip()
    email = payload.get("email", "").strip().lower()
    senha = payload.get("senha", "")
    matricula = payload.get("matricula", "").strip()
    cursos = payload.get("cursos", [])
    areas = payload.get("areas", [])
    receber_emails = payload.get("receber_emails", True)

    if not nome or len(nome) < 2:
        raise HTTPException(status_code=400, detail="Por favor, informe seu nome completo (mínimo 2 caracteres).")
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Por favor, informe um endereço de e-mail válido (ex: seu.email@gmail.com ou aluno@uern.br).")
    if not senha or len(senha) < 6:
        raise HTTPException(status_code=400, detail="A senha de acesso deve possuir no mínimo 6 caracteres.")

    if db["usuarios"].find_one({"email": email}):
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado no EduScrap. Faça login com suas credenciais ou utilize a opção 'Esqueceu sua senha?'."
        )

    novo_usuario = {
        "nome": nome,
        "email": email,
        "senha_hash": hash_password(senha),
        "matricula": matricula,
        "preferencias": {
            "cursos": cursos if isinstance(cursos, list) else [cursos],
            "areas": areas if isinstance(areas, list) else [areas],
            "receber_emails": bool(receber_emails)
        },
        "favoritos": [],
        "criado_em": datetime.now().isoformat(),
        "atualizado_em": datetime.now().isoformat()
    }

    res = db["usuarios"].insert_one(novo_usuario)
    user_id = str(res.inserted_id)
    token = generate_auth_token(user_id, email)

    novo_usuario["_id"] = user_id
    novo_usuario.pop("senha_hash", None)

    return {
        "success": True,
        "message": "Conta de estudante criada com sucesso!",
        "token": token,
        "user": novo_usuario
    }


@app.post("/api/auth/login")
def login_usuario(payload: dict):
    email = payload.get("email", "").strip().lower()
    senha = payload.get("senha", "")

    if not email or not senha:
        raise HTTPException(status_code=400, detail="E-mail e senha são obrigatórios para acessar a conta.")

    user = db["usuarios"].find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Nenhuma conta encontrada para o e-mail informado. Verifique a digitação ou cadastre-se gratuitamente."
        )

    if not verify_password(senha, user.get("senha_hash", "")):
        raise HTTPException(
            status_code=401,
            detail="Senha incorreta para este e-mail. Se esqueceu sua senha, clique em 'Esqueceu a senha?' para redefini-la."
        )

    user_id = str(user["_id"])
    token = generate_auth_token(user_id, email)

    user["_id"] = user_id
    user.pop("senha_hash", None)

    return {
        "success": True,
        "message": "Login realizado com sucesso!",
        "token": token,
        "user": user
    }


@app.post("/api/auth/redefinir-senha")
def redefinir_senha_estudante(payload: dict):
    """Permite redefinir a senha informando o e-mail cadastrado."""
    email = payload.get("email", "").strip().lower()
    nova_senha = payload.get("nova_senha", "")

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Informe um e-mail válido para redefinir a senha.")
    if not nova_senha or len(nova_senha) < 6:
        raise HTTPException(status_code=400, detail="A nova senha deve possuir no mínimo 6 caracteres.")

    user = db["usuarios"].find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma conta cadastrada com este e-mail no EduScrap. Crie sua conta gratuitamente."
        )

    novo_hash = hash_password(nova_senha)
    db["usuarios"].update_one(
        {"_id": user["_id"]},
        {"$set": {"senha_hash": novo_hash, "atualizado_em": datetime.now().isoformat()}}
    )

    return {
        "success": True,
        "message": "Senha atualizada com sucesso! Agora você já pode entrar na sua conta com a nova senha."
    }



@app.get("/api/auth/me")
def get_perfil_atual(usuario: dict = Depends(obter_usuario_logado)):
    return {"success": True, "user": usuario}


@app.put("/api/auth/preferencias")
def atualizar_preferencias(payload: dict, usuario: dict = Depends(obter_usuario_logado)):
    update_data = {}
    if "cursos" in payload:
        update_data["preferencias.cursos"] = payload["cursos"] if isinstance(payload["cursos"], list) else [payload["cursos"]]
    if "areas" in payload:
        update_data["preferencias.areas"] = payload["areas"] if isinstance(payload["areas"], list) else [payload["areas"]]
    if "receber_emails" in payload:
        update_data["preferencias.receber_emails"] = bool(payload["receber_emails"])
    update_data["atualizado_em"] = datetime.now().isoformat()

    try:
        oid = ObjectId(usuario["_id"])
    except Exception:
        oid = usuario["_id"]

    db["usuarios"].update_one({"_id": oid}, {"$set": update_data})
    user_atualizado = db["usuarios"].find_one({"_id": oid})
    user_atualizado["_id"] = str(user_atualizado["_id"])
    user_atualizado.pop("senha_hash", None)

    return {
        "success": True,
        "message": "Preferências salvas com sucesso!",
        "user": user_atualizado
    }


@app.put("/api/auth/perfil")
def atualizar_perfil(payload: dict, usuario: dict = Depends(obter_usuario_logado)):
    update_data = {}
    if "nome" in payload and str(payload["nome"]).strip():
        update_data["nome"] = str(payload["nome"]).strip()
    if "matricula" in payload:
        update_data["matricula"] = str(payload["matricula"]).strip()
    if "foto_perfil" in payload:
        update_data["foto_perfil"] = payload["foto_perfil"]
    if "curso_principal" in payload:
        update_data["curso_principal"] = str(payload["curso_principal"]).strip()
    if "campus" in payload:
        update_data["campus"] = str(payload["campus"]).strip()
    if "bio" in payload:
        update_data["bio"] = str(payload["bio"]).strip()

    # Suporte para salvar preferências simultaneamente
    if "cursos" in payload:
        update_data["preferencias.cursos"] = payload["cursos"] if isinstance(payload["cursos"], list) else [payload["cursos"]]
    if "areas" in payload:
        update_data["preferencias.areas"] = payload["areas"] if isinstance(payload["areas"], list) else [payload["areas"]]
    if "receber_emails" in payload:
        update_data["preferencias.receber_emails"] = bool(payload["receber_emails"])

    update_data["atualizado_em"] = datetime.now().isoformat()

    try:
        oid = ObjectId(usuario["_id"])
    except Exception:
        oid = usuario["_id"]

    db["usuarios"].update_one({"_id": oid}, {"$set": update_data})
    user_atualizado = db["usuarios"].find_one({"_id": oid})
    user_atualizado["_id"] = str(user_atualizado["_id"])
    user_atualizado.pop("senha_hash", None)

    return {
        "success": True,
        "message": "Perfil atualizado com sucesso!",
        "user": user_atualizado
    }


# ==========================================
# ROTAS DE FAVORITOS
# ==========================================

@app.get("/api/favoritos")
def listar_favoritos(usuario: dict = Depends(obter_usuario_logado)):
    fav_ids = usuario.get("favoritos", [])
    colecoes = [
        "vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee",
        "vagas_portal_uern", "vagas_noticias", "vagas", "editais", "noticias"
    ]
    favoritos = []

    for fid in fav_ids:
        for cname in colecoes:
            if cname not in db.list_collection_names():
                continue
            doc = None
            try:
                doc = db[cname].find_one({"_id": ObjectId(fid)})
            except Exception:
                pass
            if not doc:
                doc = db[cname].find_one({"_id": fid})
            if doc:
                doc["_id"] = str(doc["_id"])
                doc["nome"] = doc.get("titulo") or doc.get("nome") or "Oportunidade Universitária"
                doc["titulo"] = doc["nome"]
                doc = enriquecer_prazo(doc)
                doc = resolver_vinculo_fonte(doc)
                doc["favorito"] = True
                favoritos.append(doc)
                break

    return {
        "success": True,
        "count": len(favoritos),
        "data": favoritos
    }


@app.post("/api/favoritos/{id}")
def adicionar_favorito(id: str, usuario: dict = Depends(obter_usuario_logado)):
    try:
        oid = ObjectId(usuario["_id"])
    except Exception:
        oid = usuario["_id"]

    db["usuarios"].update_one(
        {"_id": oid},
        {"$addToSet": {"favoritos": str(id)}}
    )
    return {"success": True, "message": "Oportunidade adicionada aos favoritos!", "oportunidade_id": id}


@app.delete("/api/favoritos/{id}")
def remover_favorito(id: str, usuario: dict = Depends(obter_usuario_logado)):
    try:
        oid = ObjectId(usuario["_id"])
    except Exception:
        oid = usuario["_id"]

    db["usuarios"].update_one(
        {"_id": oid},
        {"$pull": {"favoritos": str(id)}}
    )
    return {"success": True, "message": "Oportunidade removida dos favoritos!", "oportunidade_id": id}

@app.get("/api/feed/personalizado")
def feed_personalizado(usuario: dict = Depends(obter_usuario_logado), limite: int = Query(50, ge=1)):
    prefs = usuario.get("preferencias", {})
    cursos = prefs.get("cursos", [])
    areas = prefs.get("areas", [])
    fav_set = set(usuario.get("favoritos", []))

    criterios_or = []
    if cursos:
        criterios_or.append({"cursos": {"$in": cursos}})
        for c in cursos:
            criterios_or.append({"nome": {"$regex": re.escape(c), "$options": "i"}})
            criterios_or.append({"titulo": {"$regex": re.escape(c), "$options": "i"}})

    if areas:
        criterios_or.append({"areas": {"$in": areas}})
        for a in areas:
            criterios_or.append({"areas": {"$regex": re.escape(a), "$options": "i"}})
            criterios_or.append({"categoria": {"$regex": re.escape(a), "$options": "i"}})
            criterios_or.append({"area": {"$regex": re.escape(a), "$options": "i"}})

    filtro = {"$or": criterios_or} if criterios_or else {}

    colecoes = ["vagas", "editais", "noticias", "vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_portal_uern"]
    resultados = []
    ids_vistos = set()

    for cname in colecoes:
        for doc in db[cname].find(filtro).limit(limite):
            doc_id = str(doc["_id"])
            if doc_id not in ids_vistos:
                ids_vistos.add(doc_id)
                doc["_id"] = doc_id
                doc = enriquecer_prazo(doc)
                doc = resolver_vinculo_fonte(doc)
                doc["favorito"] = doc_id in fav_set
                resultados.append(doc)
                if len(resultados) >= limite * 2:
                    break

    # Ordenação por relevância: se bate curso específico ganha peso 10, área ganha peso 4
    def score_relevancia(item):
        score = 0
        item_cursos = item.get("cursos", []) or []
        item_areas = item.get("areas", []) or []
        item_txt = f"{item.get('titulo', '')} {item.get('nome', '')}"

        for c in cursos:
            if c in item_cursos or re.search(re.escape(c), item_txt, re.IGNORECASE):
                score += 10

        for a in areas:
            if a in item_areas or re.search(re.escape(a), item_txt, re.IGNORECASE):
                score += 4

        return score

    resultados.sort(key=score_relevancia, reverse=True)

    # Se poucos resultados pelo filtro específico, complementa com oportunidades gerais
    if len(resultados) < 4:
        for cname in ["vagas_estagio", "editais"]:
            for doc in db[cname].find().limit(4):
                doc_id = str(doc["_id"])
                if doc_id not in ids_vistos:
                    ids_vistos.add(doc_id)
                    doc["_id"] = doc_id
                    doc = enriquecer_prazo(doc)
                    doc = resolver_vinculo_fonte(doc)
                    doc["favorito"] = doc_id in fav_set
                    resultados.append(doc)

    return {
        "success": True,
        "count": len(resultados),
        "preferencias": prefs,
        "data": resultados
    }

@app.get("/api/buscar-tudo", dependencies=[Depends(verificar_api_key)])
def acionar_todos_os_robos():
    logger.info("[SISTEMA] Iniciando a Varredura Global de Infraestrutura...")

    inicio_varredura = datetime.now()

    db["vagas_estagio"].delete_many({})
    db["vagas_bolsa"].delete_many({})
    db["vagas_ufersa"].delete_many({})
    db["vagas_ciee"].delete_many({})

    python_exe = sys.executable
    status_final = "Sucesso"
    detalhe_erro = None

    backend_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        logger.info("-> A raspar PRAE...")
        subprocess.run([python_exe, os.path.join(backend_dir, "scraper_prae.py")], cwd=backend_dir, check=False)

        logger.info("-> A raspar PROEX...")
        subprocess.run([python_exe, os.path.join(backend_dir, "scraper_proex.py")], cwd=backend_dir, check=False)

        logger.info("-> A raspar UFERSA...")
        subprocess.run([python_exe, os.path.join(backend_dir, "scraper_ufersa.py")], cwd=backend_dir, check=False)

        logger.info("-> A raspar CIEE...")
        subprocess.run([python_exe, os.path.join(backend_dir, "scraper_ciee.py")], cwd=backend_dir, check=False)

        logger.info("-> A raspar Portal UERN...")
        subprocess.run([python_exe, os.path.join(backend_dir, "scraper_portal_uern.py")], cwd=backend_dir, check=False)

        logger.info("-> A raspar Notícias...")
        atualizar_noticias_agora()

        logger.info("[MIGRAÇÃO] Rodando Normalização Heurística de Dados...")

        # Mapeia qual coleção pertence a qual chave identificadora de fonte
        mapeamento_fontes = {
            "vagas_estagio": "prae_uern",
            "vagas_bolsa": "proex_uern",
            "vagas_ufersa": "ufersa_oficial",
            "vagas_ciee": "ciee_agente",
            "vagas_portal_uern": "portal_uern_oficial"
        }

        for col_name, id_fonte in mapeamento_fontes.items():
            cursor = db[col_name].find()
            for doc in cursor:
                texto_alvo = f"{doc.get('nome', '')} {doc.get('categoria', '')}"
                data_detectada = extrair_e_converter_data(texto_alvo)

                # Monta a carga de atualização injetando a chave estrangeira (Referência)
                payload_atualizacao = {"fonte_id": id_fonte}
                if data_detectada:
                    payload_atualizacao["data_vencimento"] = data_detectada

                db[col_name].update_one(
                    {"_id": doc["_id"]},
                    {"$set": payload_atualizacao}
                )

    except Exception as e:
        status_final = "Erro"
        detalhe_erro = str(e)
        logger.error(f"[VARREDURA] Falha durante a varredura global: {e}", exc_info=True)

    fim_varredura = datetime.now()
    log_auditoria = {
        "data_execucao": inicio_varredura,
        "tempo_duracao_segundos": round((fim_varredura - inicio_varredura).total_seconds(), 2),
        "status": status_final,
        "erro": detalhe_erro,
        "documentos_importados": {
            "estagios": db["vagas_estagio"].count_documents({}),
            "bolsas": db["vagas_bolsa"].count_documents({}),
            "ufersa": db["vagas_ufersa"].count_documents({}),
            "noticias": db["vagas_noticias"].count_documents({}),
            "portal_uern": db["vagas_portal_uern"].count_documents({})
        }
    }

    db["historico_varreduras"].insert_one(log_auditoria)

    if status_final == "Erro":
        return {"erro": detalhe_erro}

    return {"mensagem": "Varredura global concluída e normatizada com sucesso!"}


# =====================================================================
# Módulo de Governança Técnica e Painel Administrativo (UC11, UC12, RF12)
# =====================================================================

CONFIG_DIR = os.path.join(BACKEND_DIR, "..", "config")
PATTERNS_FILE = os.path.join(CONFIG_DIR, "patterns.json")
COURSE_MAPPING_FILE = os.path.join(CONFIG_DIR, "course_mapping.json")

def _validar_url_segura(url: str) -> bool:
    """
    Mitigação de SSRF (Seção 16 do Documento):
    Valida se a URL usa protocolo seguro http/https e não aponta para endereços internos restritos.
    """
    if not url or not isinstance(url, str):
        return False
    url_l = url.strip().lower()
    if not (url_l.startswith("http://") or url_l.startswith("https://")):
        return False
    proibidos = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.", "10.", "192.168."]
    for p in proibidos:
        if p in url_l:
            return False
    return True

@app.get("/api/admin/regras")
def obter_regras_extracao(admin: dict = Depends(verificar_admin)):
    """UC12 / RF12: Consulta regras de extração (Regex e padrões) sem recompilar."""
    try:
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            conteudo = json.load(f)
        return {"sucesso": True, "regras": conteudo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler regras: {e}")

@app.put("/api/admin/regras")
def atualizar_regras_extracao(payload: dict, admin: dict = Depends(verificar_admin)):
    """UC12 / RF12: Atualiza regras de extração no disco para efeito imediato na próxima coleta."""
    if not payload:
        raise HTTPException(status_code=400, detail="Payload inválido")
    try:
        with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Regras de extração atualizadas pelo administrador ({admin.get('nome', 'admin')}).")
        return {"sucesso": True, "mensagem": "Regras atualizadas com sucesso! Válidas a partir da próxima coleta."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gravar regras: {e}")

@app.get("/api/admin/fontes")
def listar_fontes_configuradas(admin: dict = Depends(verificar_admin)):
    """UC12: Lista fontes cadastradas e seus parâmetros de varredura."""
    from run_scrapers import SCRAPERS
    return {
        "sucesso": True,
        "total_fontes": len(SCRAPERS),
        "fontes": SCRAPERS
    }

@app.get("/api/admin/logs")
def listar_logs_robos(admin: dict = Depends(verificar_admin)):
    """UC11: Consulta logs isolados de cada robô de coleta."""
    logs_dir = os.path.join(BACKEND_DIR, "..", "logs")
    if not os.path.exists(logs_dir):
        return {"sucesso": True, "logs": []}
    arquivos = []
    for nome in os.listdir(logs_dir):
        if nome.endswith(".log"):
            caminho = os.path.join(logs_dir, nome)
            tamanho_kb = round(os.path.getsize(caminho) / 1024, 1)
            mtime = datetime.fromtimestamp(os.path.getmtime(caminho)).strftime("%Y-%m-%d %H:%M:%S")
            arquivos.append({
                "arquivo": nome,
                "tamanho_kb": tamanho_kb,
                "ultima_modificacao": mtime
            })
    return {"sucesso": True, "logs": arquivos}

@app.get("/api/admin/logs/{arquivo}")
def visualizar_conteudo_log(arquivo: str, admin: dict = Depends(verificar_admin)):
    """UC11: Exibe o conteúdo das últimas linhas do log do robô."""
    if ".." in arquivo or "/" in arquivo or "\\" in arquivo:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")
    caminho = os.path.join(BACKEND_DIR, "..", "logs", arquivo)
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo de log não encontrado.")
    try:
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
        ultimas_linhas = "".join(linhas[-200:])
        return {"sucesso": True, "arquivo": arquivo, "linhas": ultimas_linhas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler log: {e}")



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
    )