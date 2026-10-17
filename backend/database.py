import os
import logging
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger("database.mongo")

class MongoDatabase:
    """
    Camada de Persistência (MongoDB) conforme modelagem de classes (Figura 11).
    Gerencia conexão, índices e operações de upsert polimórfico de oportunidades.
    """
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = db_name or os.getenv("MONGODB_DB", "hub_estudantes")
        self.client: MongoClient = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
        self.db: Database = self.client[self.db_name]
        self.oportunidades: Collection = self.db["oportunidades"]
        self.usuarios: Collection = self.db["usuarios"]

    def criar_indices_busca(self) -> None:
        """Cria índices compostos textuais e temporais para consultas instantâneas (RNF01)"""
        try:
            self.oportunidades.create_index([
                ("titulo", TEXT),
                ("descricao", TEXT),
                ("tags", TEXT)
            ], name="idx_busca_textual")

            self.oportunidades.create_index([("link", ASCENDING)], unique=True, name="idx_link_canonico")
            self.oportunidades.create_index([("data_limite", ASCENDING)], name="idx_data_limite")
            self.oportunidades.create_index([("fonte", ASCENDING)], name="idx_fonte")
            self.oportunidades.create_index([("status_vigencia", ASCENDING)], name="idx_status_vigencia")

            self.usuarios.create_index([("email", ASCENDING)], unique=True, name="idx_email_unico")
            logger.info("Índices de busca criados com sucesso no MongoDB")
        except Exception as e:
            logger.warning(f"Aviso ao criar índices no MongoDB: {e}")

    def criar_indices_banco(self) -> None:
        """Alias para compatibilidade com o diagrama de classes"""
        self.criar_indices_busca()

    def upsert_oportunidade(self, filtro: Dict[str, Any], doc: Dict[str, Any]) -> Any:
        """
        Insere ou atualiza (upsert) a oportunidade com base no link canônico (RN04).
        """
        try:
            return self.oportunidades.update_one(
                filtro,
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Erro no upsert da oportunidade: {e}")
            raise

    def get_collection(self, nome: str) -> Collection:
        return self.db[nome]

# Instância singleton padrão para reutilização
_db_instance: Optional[MongoDatabase] = None

def get_mongo_database() -> MongoDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = MongoDatabase()
    return _db_instance
