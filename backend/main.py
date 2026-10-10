##backend/main.py 
import logging
import os
import subprocess
import sys
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

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

app = FastAPI(title="API TechHub UERN")

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
    """
    Executa a junção lógica baseada em referência (DBRef Manual) em tempo
    de execução, agregando os metadados ricos da instituição ao edital.
    """
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
    return {"mensagem": "A API do TechHub está online! Acesse /docs para testar."}

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

    # Agrupa oportunidades da UFERSA (PROAE e CPPS)
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
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["editais"]
    pulo = (pagina - 1) * limite

    filtro = {"fonte": {"$regex": "IFRN", "$options": "i"}}
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
    authorization: str = Header(default=None)
):
    usuario = obter_usuario_opcional(authorization)
    colecao = db["vagas"]
    pulo = (pagina - 1) * limite

    filtro = {"fonte": {"$regex": "IEL", "$options": "i"}}
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

    colecao = db["vagas_noticias"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_noticias = []
    for noticia in colecao.find(filtro).skip(pulo).limit(limite):
        noticia["_id"] = str(noticia["_id"])
        noticia = enriquecer_doc(noticia, usuario)
        lista_noticias.append(noticia)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_noticias
    }

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
    totais = {
        "estagios": db["vagas_estagio"].count_documents({}),
        "bolsas": db["vagas_bolsa"].count_documents({}),
        "ufersa": db["vagas_ufersa"].count_documents({}),
        "ciee": db["vagas_ciee"].count_documents({}),
        "noticias": db["vagas_noticias"].count_documents({}),
        "portal_uern": db["vagas_portal_uern"].count_documents({}) # Alimentação do novo contador do card
    }

    agora = datetime.now()
    janela_limite = agora + timedelta(days=7)

    query_reta_final = {
        "data_vencimento": {
            "$gte": agora,
            "$lte": janela_limite
        }
    }

    total_reta_final = (
        db["vagas_estagio"].count_documents(query_reta_final) +
        db["vagas_bolsa"].count_documents(query_reta_final) +
        db["vagas_ufersa"].count_documents(query_reta_final) +
        db["vagas_ciee"].count_documents(query_reta_final)
    )

    pipeline_prae = [
        {"$group": {"_id": "$categoria", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    distribuicao_prae = list(db["vagas_estagio"].aggregate(pipeline_prae))
    formatar = lambda lista: [{"categoria": item["_id"] if item["_id"] else "Geral / Não Especificada", "total": item["total"]} for item in lista]

    return {
        "totais": totais,
        "reta_final_urgente": total_reta_final,
        "prae_categorias": formatar(distribuicao_prae)
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

@app.post("/api/auth/register")
def register_usuario(payload: dict):
    nome = payload.get("nome", "").strip()
    email = payload.get("email", "").strip().lower()
    senha = payload.get("senha", "")
    matricula = payload.get("matricula", "").strip()
    cursos = payload.get("cursos", [])
    areas = payload.get("areas", [])
    receber_emails = payload.get("receber_emails", True)

    if not nome:
        raise HTTPException(status_code=400, detail="Nome é obrigatório")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email válido é obrigatório")
    if not senha or len(senha) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 6 caracteres")

    if db["usuarios"].find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Já existe uma conta cadastrada com este email.")

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
        "message": "Conta criada com sucesso!",
        "token": token,
        "user": novo_usuario
    }


@app.post("/api/auth/login")
def login_usuario(payload: dict):
    email = payload.get("email", "").strip().lower()
    senha = payload.get("senha", "")

    if not email or not senha:
        raise HTTPException(status_code=400, detail="Email e senha são obrigatórios")

    user = db["usuarios"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not verify_password(senha, user.get("senha_hash", "")):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

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
    if "nome" in payload and payload["nome"].strip():
        update_data["nome"] = payload["nome"].strip()
    if "matricula" in payload:
        update_data["matricula"] = payload["matricula"].strip()
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
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_portal_uern", "vagas_noticias"]
    favoritos = []

    for fid in fav_ids:
        for cname in colecoes:
            doc = None
            try:
                doc = db[cname].find_one({"_id": ObjectId(fid)})
            except Exception:
                pass
            if not doc:
                doc = db[cname].find_one({"_id": fid})
            if doc:
                doc["_id"] = str(doc["_id"])
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
    )