from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import subprocess
import sys
from datetime import datetime, timedelta

# Importa a função de raspagem assíncrona de notícias
from scraper_noticias import atualizar_noticias_agora

app = FastAPI(title="API TechHub UERN")

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017/")
db = client["hub_estudantes"]

# Rota de teste
@app.get("/")
def raiz():
    return {"mensagem": "A API do TechHub está online! Acesse /docs para testar."}

# ====================================================================
# ROTAS COM PAGINAÇÃO ATIVA EM NÍVEL DE CURSOR NO MONGODB ($skip e $limit)
# ====================================================================

@app.get("/api/estagios")
def listar_estagios(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1)):
    """
    Retorna os estágios da PRAE aplicando paginação nativa em disco com skip e limit.
    """
    colecao = db["vagas_estagio"]
    
    # Cálculo matemático do pulo de documentos baseado na página atual
    pulo = (pagina - 1) * limite
    
    lista_vagas = []
    # O banco executa o skip e o limit antes de trazer os documentos para o Python
    for vaga in colecao.find().skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        lista_vagas.append(vaga)
        
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents({}),
        "dados": lista_vagas
    }

@app.get("/api/bolsas")
def listar_bolsas(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1)):
    """
    Retorna as bolsas da PROEX aplicando paginação nativa.
    """
    colecao = db["vagas_bolsa"]
    pulo = (pagina - 1) * limite
    
    lista_bolsas = []
    for bolsa in colecao.find().skip(pulo).limit(limite):
        bolsa["_id"] = str(bolsa["_id"])
        lista_bolsas.append(bolsa)
        
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents({}),
        "dados": lista_bolsas
    }

@app.get("/api/ufersa")
def listar_ufersa(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1)):
    """
    Retorna os editais da UFERSA aplicando paginação nativa.
    """
    colecao = db["vagas_ufersa"]
    pulo = (pagina - 1) * limite
    
    lista_ufersa = []
    for edital in colecao.find().skip(pulo).limit(limite):
        edital["_id"] = str(edital["_id"])
        lista_ufersa.append(edital)
        
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents({}),
        "dados": lista_ufersa
    }

@app.get("/api/ciee")
def listar_ciee(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1)):
    """
    Retorna as vagas do CIEE aplicando paginação nativa.
    """
    colecao = db["vagas_ciee"]
    pulo = (pagina - 1) * limite
    
    lista_ciee = []
    for vaga in colecao.find().skip(pulo).limit(limite):
        vaga["_id"] = str(vaga["_id"])
        lista_ciee.append(vaga)
        
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents({}),
        "dados": lista_ciee
    }


# ====================================================================
# RECURSO AVANÇADO DE CACHE INTELIGENTE POR TIMESTAMP (TTL CONTROL)
# ====================================================================
@app.get("/api/noticias")
def listar_noticias(pagina: int = Query(1, ge=1), limite: int = Query(6, ge=1)):
    """
    Evita requisições abusivas e repetitivas a portais externos controlando
    um ciclo de vida (TTL) de cache de 10 minutos persistido no MongoDB.
    """
    colecao_cache = db["controle_cache"]
    ultimo_registro = colecao_cache.find_one({"tipo": "noticias"})
    
    tempo_limite = datetime.now() - timedelta(minutes=10)
    
    if not ultimo_registro or ultimo_registro["data_execucao"] < tempo_limite:
        print("[CACHE] Cache expirado ou inexistente. A acionar robô de notícias...")
        atualizar_noticias_agora()
        
        colecao_cache.update_one(
            {"tipo": "noticias"},
            {"$set": {"data_execucao": datetime.now()}},
            upsert=True
        )
    else:
        print("[CACHE] Dados recuperados localmente via cache ativo do MongoDB.")
    
    colecao = db["vagas_noticias"]
    pulo = (pagina - 1) * limite
    
    lista_noticias = []
    for noticia in colecao.find().skip(pulo).limit(limite):
        noticia["_id"] = str(noticia["_id"])
        lista_noticias.append(noticia)
        
    return {
        "pagina_atual": pagina,
        "limite_por_pagina": limite,
        "total_documentos": colecao.count_documents({}),
        "dados": lista_noticias
    }


# ==========================================
# RECURSOS DE INFRAESTRUTURA & PESQUISA
# ==========================================

@app.get("/api/pesquisar")
def pesquisar_unificado(termo: str = Query(..., min_length=2)):
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee"]
    resultados = []
    
    for col_name in db.list_collection_names():
        if col_name in colecoes:
            try:
                cursor = db[col_name].find({"$text": {"$search": termo}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    resultados.append(doc)
            except Exception:
                cursor = db[col_name].find({"nome": {"$regex": termo, "$options": "i"}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    resultados.append(doc)
    return resultados

@app.get("/api/estatisticas")
def obter_estatisticas():
    totais = {
        "estagios": db["vagas_estagio"].count_documents({}),
        "bolsas": db["vagas_bolsa"].count_documents({}),
        "ufersa": db["vagas_ufersa"].count_documents({}),
        "ciee": db["vagas_ciee"].count_documents({}),
        "noticias": db["vagas_noticias"].count_documents({})
    }
    
    pipeline_prae = [
        {"$group": {"_id": "$categoria", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    distribuicao_prae = list(db["vagas_estagio"].aggregate(pipeline_prae))
    
    formatar = lambda lista: [{"categoria": item["_id"] if item["_id"] else "Geral / Não Especificada", "total": item["total"]} for item in lista]
    
    return {
        "totais": totais,
        "prae_categorias": formatar(distribuicao_prae)
    }

@app.get("/api/db-status")
def obter_status_do_banco():
    status_colecoes = []
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_noticias", "historico_varreduras"]
    
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


# ====================================================================
# RECURSO AVANÇADO DE GOVERNANÇA, LOGS E AUDITORIA DE RASPAGEM
# ====================================================================
@app.get("/api/buscar-tudo")
def acionar_todos_os_robos():
    print("\n[SISTEMA] Iniciando a Varredura Global de Infraestrutura...")
    
    inicio_varredura = datetime.now()
    
    db["vagas_estagio"].delete_many({})
    db["vagas_bolsa"].delete_many({})
    db["vagas_ufersa"].delete_many({})
    db["vagas_ciee"].delete_many({})
    
    python_exe = sys.executable
    status_final = "Sucesso"
    detalhe_erro = None
    
    try:
        print("-> A raspar PRAE...")
        subprocess.run([python_exe, "scraper_prae.py"])
        
        print("-> A raspar PROEX...")
        subprocess.run([python_exe, "scraper_proex.py"])
        
        print("-> A raspar UFERSA...")
        subprocess.run([python_exe, "scraper_ufersa.py"])
        
        print("-> A raspar CIEE (Atenção ao navegador!)...")
        subprocess.run([python_exe, "scraper_ciee.py"])
        
        print("-> A raspar Notícias...")
        atualizar_noticias_agora()
        
    except Exception as e:
        status_final = "Erro"
        detalhe_erro = str(e)
    
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
            "noticias": db["vagas_noticias"].count_documents({})
        }
    }
    
    db["historico_varreduras"].insert_one(log_auditoria)
    
    if status_final == "Erro":
        return {"erro": detalhe_erro}
        
    return {"mensagem": "Varredura global concluída e registada com sucesso na base de logs!"}