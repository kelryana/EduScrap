from pymongo import MongoClient

# Conecta ao MongoDB que está rodando na sua própria máquina (localhost) na porta padrão (27017)
client = MongoClient("mongodb://localhost:27017/")

# Cria (ou acessa) o banco de dados do seu projeto
db = client["hub_estudantes"]

# Cria (ou acessa) a coleção onde ficarão os links raspados
colecao_vagas = db["vagas_estagio"]

# Exemplo de inserção simples para testar
dados_teste = {
    "titulo": "Estágio de Analista em Python",
    "link": "https://exemplo.com/vaga2",
    "categoria": "Carteira Assinada",
    "data" : "02/06/2006"
}

colecao_vagas.insert_one(dados_teste)
print("Dado inserido localmente com sucesso!")