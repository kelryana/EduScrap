from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

# Cria a aplicação FastAPI
app = FastAPI(title="API TechHub UERN")

# Configuração do CORS (MUITO IMPORTANTE para o Front-end)
# Isso permite que o seu site HTML "puxe" os dados sem dar erro de permissão
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Na fase de testes, permite qualquer origem
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conecta ao MongoDB local
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