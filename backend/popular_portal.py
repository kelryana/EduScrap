from pymongo import MongoClient
from datetime import datetime

# Configurações de Conexão NoSQL do seu ecossistema
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "hub_estudantes"

def semear_dados_portal():
    print("🌱=== INICIANDO DATA SEEDING (CONTINGÊNCIA DEFINTIVA) ===")
    
    # 1. Estabelece a conexão com o banco local
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    colecao = db["vagas_portal_uern"]
    
    # 2. Limpa preventivamente a coleção para não duplicar dados
    print("🧹 Expurgando registros antigos de 'vagas_portal_uern'...")
    colecao.delete_many({})
    
    # 3. Massa de dados realistas com datetime local para o formatador do main.py não quebrar
    dados_minerados = [
        {
            "nome": "Uern abre matrículas para cursos de idiomas e cursos preparatórios de proficiência do NEEL",
            "link": "https://portal.uern.br/blog/uern-abre-matriculas-para-cursos-de-idiomas-e-cursos-preparatorios-de-proficiencia-do-neel/",
            "categoria": "Edital Interno",
            "fonte_id": "portal_uern_oficial",
            "data_vencimento": datetime.now()
        },
        {
            "nome": "Estudantes podem manifestar interesse em estagiar nos Jogos Universitários da Uern",
            "link": "https://portal.uern.br/blog/estudantes-podem-manifestar-interesse-em-estagiar-nos-jogos-universitarios-da-uern/",
            "categoria": "Seleção de Estágio",
            "fonte_id": "portal_uern_oficial",
            "data_vencimento": datetime.now()
        },
        {
            "nome": "Uern abre seleção de estágio para estudantes de outras instituições de ensino superior",
            "link": "https://portal.uern.br/blog/uern-abre-selecao-de-estagio-para-estudantes-de-outras-instituicoes-de-ensino-superior/",
            "categoria": "Seleção de Estágio",
            "fonte_id": "portal_uern_oficial",
            "data_vencimento": datetime.now()
        }
    ]
    
    # 4. Insere a carga estruturada no cluster NoSQL
    print("🚀 Injetando documentos normalizados no banco...")
    colecao.insert_many(dados_minerados)
    
    print("-" * 65)
    print(f"✅ SUCESSO! 3 oportunidades legítimas persistidas no MongoDB.")
    print("🎓 A aba 'Editais UERN' está abastecida e blindada!")
    print("🌱=== PROCESSO DE ENGENHARIA DE DADOS FINALIZADO ===")

if __name__ == "__main__":
    semear_dados_portal()