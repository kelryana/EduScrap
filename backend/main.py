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

from scraper_noticias import atualizar_noticias_agora

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
    """Dependência FastAPI: exige o header X-API-Key válido."""
    if not API_KEY:
        # Proteção desativada (apenas desenvolvimento local sem API_KEY no .env)
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
def garantir_metadados_fontes():
    
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


# Rota de teste
@app.get("/")
def raiz():
    return {"mensagem": "A API do TechHub está online! Acesse /docs para testar."}

@app.get("/api/estagios")
def listar_estagios(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
    colecao = db["vagas_estagio"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_vagas = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        vaga = enriquecer_prazo(vaga)

        vaga = resolver_vinculo_fonte(vaga)
        lista_vagas.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_vagas
    }

@app.get("/api/bolsas")
def listar_bolsas(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
    colecao = db["vagas_bolsa"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_bolsas = []
    for bolsa in colecao.find(filtro).skip(pulo).limit(limite):
        bolsa["_id"] = str(bolsa["_id"])
        bolsa = enriquecer_prazo(bolsa)

        bolsa = resolver_vinculo_fonte(bolsa)
        lista_bolsas.append(bolsa)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_bolsas
    }

@app.get("/api/ufersa")
def listar_ufersa(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
    colecao = db["vagas_ufersa"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_ufersa = []
    for edital in colecao.find(filtro).skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        edital = enriquecer_prazo(edital)

        edital = resolver_vinculo_fonte(edital)
        lista_ufersa.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_ufersa
    }

@app.get("/api/ciee")
def listar_ciee(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
    colecao = db["vagas_ciee"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_ciee = []
    for vaga in colecao.find(filtro).skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])

        vaga["nome"] = vaga.get("nome_completo") or vaga.get("titulo") or "Vaga CIEE"

        vaga = enriquecer_prazo(vaga)

        vaga = resolver_vinculo_fonte(vaga)
        lista_ciee.append(vaga)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_ciee
    }

@app.get("/api/portal_uern")
def listar_portal_uern(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
    colecao = db["vagas_portal_uern"]
    pulo = (pagina - 1) * limite

    filtro = {}
    if apenas_vigentes:
        filtro["data_vencimento"] = {"$gte": datetime.now()}

    lista_portal = []
    for edital in colecao.find(filtro).skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        edital = enriquecer_prazo(edital)

        edital = resolver_vinculo_fonte(edital)
        lista_portal.append(edital)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_portal
    }


@app.get("/api/noticias")
def listar_noticias(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1), apenas_vigentes: bool = False):
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
        noticia = enriquecer_prazo(noticia)
        lista_noticias.append(noticia)

    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents(filtro),
        "dados": lista_noticias
    }

@app.get("/api/pesquisar")
def pesquisar_unificado(termo: str = Query(..., min_length=2)):
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_portal_uern"]
    resultados = []
    for col_name in db.list_collection_names():
        if col_name in colecoes:
            try:
                cursor = db[col_name].find({"$text": {"$search": termo}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    doc = enriquecer_prazo(resolver_vinculo_fonte(doc))
                    resultados.append(doc)
            except Exception:
                cursor = db[col_name].find({"nome": {"$regex": termo, "$options": "i"}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    doc = enriquecer_prazo(resolver_vinculo_fonte(doc))
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

    try:
        logger.info("-> A raspar PRAE...")
        subprocess.run([python_exe, "scraper_prae.py"])

        logger.info("-> A raspar PROEX...")
        subprocess.run([python_exe, "scraper_proex.py"])

        logger.info("-> A raspar UFERSA...")
        subprocess.run([python_exe, "scraper_ufersa.py"])

        logger.info("-> A raspar CIEE...")
        subprocess.run([python_exe, "scraper_ciee.py"])

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