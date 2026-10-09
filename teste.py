from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["hub_estudantes"]

colecao_vagas = db["vagas_estagio"]

dados_teste = {
    "titulo": "Estágio de Analista em Python",
    "link": "https://exemplo.com/vaga2",
    "categoria": "Carteira Assinada",
    "data" : "02/06/2006"
}

colecao_vagas.insert_one(dados_teste)
print("Dado inserido localmente com sucesso!")