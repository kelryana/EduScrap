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

    print("\n" + "="*60)
    logger.info("SISTEMA OTIMIZADO COM SUCESSO!")
    print("="*60 + "\n")

if __name__ == "__main__":
    configurar_banco_avancado()

    
    