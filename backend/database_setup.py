#backend/database_setup.py

from pymongo import MongoClient
import logging
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

def configurar_banco_avancado():
    print("\n" + "="*60)
    logger.info("=== [DATABASE SETUP] CONFIGURAÇÃO FÍSICA E OTIMIZAÇÃO DO MONGODB ===")
    print("="*60)

    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    colecoes = ["vagas_estagio", "vagas_bolsa", "vagas_ufersa", "vagas_ciee"]

    for col_name in colecoes:
        colecao = db[col_name]

        logger.info(f"-> Criando Índice de Texto ($text) na coleção: {col_name}...")
        colecao.create_index([("nome", "text")], name="idx_busca_nome_text")

        logger.info(f"-> Criando Índice Composto (categoria + fonte) na coleção: {col_name}...")
        colecao.create_index([("categoria", 1), ("fonte", 1)], name="idx_categoria_fonte")

    logger.info("-> Associando validador estrito JSON Schema na coleção 'vagas_noticias'...")
    try:
        db.command({
            "collMod": "vagas_noticias",
            "validator": {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["nome", "link", "fonte", "categoria"],
                    "properties": {
                        "nome": {
                            "bsonType": "string",
                            "description": "O título da vaga ou notícia é obrigatório"
                        },
                        "link": {
                            "bsonType": "string",
                            "pattern": "^https?://",
                            "description": "O link deve ser uma URL válida"
                        },
                        "fonte": {
                            "bsonType": "string",
                            "description": "A fonte identificadora é obrigatória"
                        },
                        "categoria": {
                            "bsonType": "string",
                            "description": "A categoria do edital é obrigatória"
                        }
                    }
                }
            },
            "validationAction": "warn"
        })
        logger.info("JSON Schema acoplado com sucesso!")
    except Exception as e:
        logger.info(f"Nota do Validador: {e}")

    # Migração / Correção de links genéricos do CIEE para a página individual da vaga
    try:
        import re
        col_ciee = db["vagas_ciee"]
        docs_ciee = list(col_ciee.find({"link": {"$in": ["https://portal.ciee.org.br/", "https://portal.ciee.org.br", "", None]}}))
        migrados = 0
        for doc in docs_ciee:
            cod = doc.get("codigo")
            if not cod or cod == "N/A":
                match = re.search(r"\[(\d{6,})\]", doc.get("nome", "") or doc.get("titulo", ""))
                if match:
                    cod = match.group(1)
            novo_link = f"https://portal.ciee.org.br/quero-uma-vaga/?codigoVaga={cod}" if cod and cod != "N/A" else "https://portal.ciee.org.br/quero-uma-vaga/"
            col_ciee.update_one({"_id": doc["_id"]}, {"$set": {"link": novo_link}})
            migrados += 1
        if migrados > 0:
            logger.info(f"-> Migrados {migrados} links do CIEE para páginas individuais de estágio.")
    except Exception as e:
        logger.warning(f"Nota na migração de links CIEE: {e}")

    print("\n" + "="*60)
    logger.info("SISTEMA OTIMIZADO COM SUCESSO!")
    print("="*60 + "\n")

if __name__ == "__main__":
    configurar_banco_avancado()

    
    