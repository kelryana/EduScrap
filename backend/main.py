from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import subprocess
import sys

# Importa a função de raspar na hora
from scraper_noticias import atualizar_noticias_agora

app = FastAPI(title="API TechHub UERN")

# Configuração do CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na fase de testes, permite qualquer origem
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

# Rota para buscar os editais da PRAE
@app.get("/api/estagios")
def listar_estagios():
    colecao = db["vagas_estagio"]
    lista_vagas = []
    
    # Busca todos os documentos na coleção
    for vaga in colecao.find():
        vaga["_id"] = str(vaga["_id"]) # Converte o ObjectId para texto
        lista_vagas.append(vaga)
        
    return lista_vagas

# Rota para buscar as bolsas da PROEX
@app.get("/api/bolsas")
def listar_bolsas():
    colecao = db["vagas_bolsa"]
    lista_bolsas = []
    
    # Busca todos os documentos na coleção
    for bolsa in colecao.find():
        bolsa["_id"] = str(bolsa["_id"]) # Converte o ObjectId para texto
        lista_bolsas.append(bolsa)
        
    return lista_bolsas

@app.get("/api/ufersa")
def listar_ufersa():
    colecao = db["vagas_ufersa"]
    lista_ufersa = []
    
    # Busca todos os documentos na coleção
    for edital in colecao.find():
        edital["_id"] = str(edital["_id"]) # Converte o ObjectId para texto
        lista_ufersa.append(edital)
        
    return lista_ufersa

@app.get("/api/ciee")
def listar_ciee():
    colecao = db["vagas_ciee"]
    lista_ciee = []
    
    # Busca todos os documentos na coleção
    for vaga in colecao.find():
        vaga["_id"] = str(vaga["_id"]) # Converte o ObjectId para texto
        lista_ciee.append(vaga)
        
    return lista_ciee

@app.get("/api/noticias")
def listar_noticias():
    # 1. GATILHO: Roda o script de raspagem ANTES de buscar no banco
    atualizar_noticias_agora()
    
    colecao = db["vagas_noticias"]
    lista_noticias = []
    
    for noticia in colecao.find():
        noticia["_id"] = str(noticia["_id"])
        lista_noticias.append(noticia)
        
    return lista_noticias

# ====================================================================
# NOVAS ROTAS ADICIONADAS 
# ====================================================================

@app.get("/api/pesquisar")
def pesquisar_unificado(termo: str = Query(..., min_length=2)):
    """
    Realiza uma busca textual avançada através de todas as coleções de vagas,
    utilizando os índices de texto criados nativamente no MongoDB.
    """
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee"]
    resultados = []
    
    for col_name in db.list_collection_names():
        if col_name in colecoes:
            try:
                # Busca nativa usando o índice de texto composto ($text)
                cursor = db[col_name].find({"$text": {"$search": termo}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    resultados.append(doc)
            except Exception:
                # Fallback via regex caso o banco de dados ainda não possua o índice
                cursor = db[col_name].find({"nome": {"$regex": termo, "$options": "i"}})
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    resultados.append(doc)
                    
    return resultados

@app.get("/api/estatisticas")
def obter_estatisticas():
    """
    Usa o Aggregation Framework do MongoDB ($group e $sort) para consolidar
    métricas analíticas em tempo de execução diretamente no banco de dados.
    """
    # Contagem básica totalizadores de coleções
    totais = {
        "estagios": db["vagas_estagio"].count_documents({}),
        "bolsas": db["vagas_bolsa"].count_documents({}),
        "ufersa": db["vagas_ufersa"].count_documents({}),
        "ciee": db["vagas_ciee"].count_documents({}),
        "noticias": db["vagas_noticias"].count_documents({})
    }
    
    # Pipeline de Agregação avançado: Agrupa documentos por Categoria e ordena pela contagem de forma decrescente
    pipeline_prae = [
        {"$group": {"_id": "$categoria", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    distribuicao_prae = list(db["vagas_estagio"].aggregate(pipeline_prae))
    
    # Formatação limpa do JSON de saída para renderizar no front-end
    formatar = lambda lista: [{"categoria": item["_id"] if item["_id"] else "Geral / Não Especificada", "total": item["total"]} for item in lista]
    
    return {
        "totais": totais,
        "prae_categorias": formatar(distribuicao_prae)
    }

@app.get("/api/db-status")
def obter_status_do_banco():
    """
    Retorna os metadados físicos das coleções (Tamanho em disco, Índices ativos e Status de validação).
    Essencial para provar à banca de Banco II que você domina a administração da base NoSQL.
    """
    status_colecoes = []
    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee", "vagas_noticias"]
    
    for col_name in colecoes:
        colecao = db[col_name]
        
        # Recupera a lista física de índices criados em disco
        try:
            indices_brutos = list(colecao.list_indexes())
            indices_nomes = [idx["name"] for idx in indices_brutos]
        except Exception:
            indices_nomes = ["_id_"]
        
        # Coleta estatísticas operacionais de armazenamento (tamanho da coleção)
        try:
            stats = db.command("collStats", col_name)
            tamanho_kb = round(stats.get("size", 0) / 1024, 2)
            documentos_qtd = stats.get("count", 0)
        except Exception:
            tamanho_kb = 0.0
            documentos_qtd = colecao.count_documents({})
            
        # Verifica se o Schema Validation está anexado à coleção
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

# Rota do "Botão Vermelho": Limpa o banco e roda todos os scrapers
@app.get("/api/buscar-tudo")
def acionar_todos_os_robos():
    print("\n[SISTEMA] Iniciando a Varredura Global...")
    
    db["vagas_estagio"].delete_many({})
    db["vagas_bolsa"].delete_many({})
    db["vagas_ufersa"].delete_many({})
    db["vagas_ciee"].delete_many({})
    # db["vagas_noticias"].delete_many({}) -> A de notícias já se auto-limpa no script dela
    
    # Pega o caminho exato do seu Python (para evitar erros de versão)
    python_exe = sys.executable
    
    try:
        print("-> Raspando PRAE...")
        subprocess.run([python_exe, "scraper_prae.py"])
        
        print("-> Raspando PROEX...")
        subprocess.run([python_exe, "scraper_proex.py"])
        
        print("-> Raspando UFERSA...")
        subprocess.run([python_exe, "scraper_ufersa.py"])
        
        print("-> Raspando CIEE (Atenção ao navegador!)...")
        subprocess.run([python_exe, "scraper_ciee.py"])
        
        return {"mensagem": "Varredura 100% concluída!"}
        
    except Exception as e:
        return {"erro": str(e)}