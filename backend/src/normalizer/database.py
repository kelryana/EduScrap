# src/normalizer/database.py

from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBHandler:
    def __init__(self, uri: str = None, db_name: str = "hub_estudantes"):
      
        self.uri = uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = db_name
        self.client = None
        self.db = None
        self._connect()

    def _connect(self) -> None:
        """Estabelece conexão com MongoDB"""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=45000,
                connectTimeoutMS=20000
            )
            # Testa a conexão
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.info(f"Conexão estabelecida com MongoDB: {self.db_name}")
        except ConnectionFailure as e:
            logger.error(f"Falha na conexão com MongoDB: {str(e)}")
            raise

    def create_indexes(self) -> None:
        """Cria índices otimizados para consultas frequentes"""
        try:
            # Coleção de editais
            editais = self.db['editais']
            editais.create_index([("status", ASCENDING)], name="idx_status")
            editais.create_index([("areas", ASCENDING)], name="idx_areas")
            editais.create_index([("data_limite", ASCENDING)], name="idx_data_limite")
            editais.create_index([("titulo", TEXT)], name="idx_busca_titulo")
            editais.create_index([("status", ASCENDING), ("areas", ASCENDING)],
                               name="idx_status_areas_composto")

            # Coleção de vagas
            vagas = self.db['vagas']
            vagas.create_index([("area", ASCENDING)], name="idx_area")
            vagas.create_index([("fonte", ASCENDING)], name="idx_fonte")
            vagas.create_index([("titulo", TEXT)], name="idx_busca_titulo_vaga")

            # Coleção de notícias
            noticias = self.db['noticias']
            noticias.create_index([("categoria", ASCENDING)], name="idx_categoria")
            noticias.create_index([("data_publicacao", ASCENDING)], name="idx_data_pub")
            noticias.create_index([("titulo", TEXT)], name="idx_busca_titulo_noticia")

            logger.info("Índices criados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar índices: {str(e)}")

    def insert_edital(self, edital_ Dict[str, Any]) -> Optional[str]:
    
        try:
            edital_data['atualizado_em'] = datetime.now().isoformat()
            result = self.db['editais'].insert_one(edital_data)
            logger.info(f"Edital inserido com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except DuplicateKeyError:
            logger.warning(f"Edital duplicado: {edital_data.get('titulo')}")
            return None
        except Exception as e:
            logger.error(f"Erro ao inserir edital: {str(e)}")
            return None

    def insert_vaga(self, vaga_ Dict[str, Any]) -> Optional[str]:
     
        try:
            vaga_data['atualizado_em'] = datetime.now().isoformat()
            result = self.db['vagas'].insert_one(vaga_data)
            logger.info(f"Vaga inserida com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir vaga: {str(e)}")
            return None

    def insert_noticia(self, noticia_ Dict[str, Any]) -> Optional[str]:
     
        try:
            noticia_data['atualizado_em'] = datetime.now().isoformat()
            result = self.db['noticias'].insert_one(noticia_data)
            logger.info(f"Notícia inserida com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir notícia: {str(e)}")
            return None

    def get_oportunidades(
        self,
        area: Optional[str] = None,
        status: Optional[str] = None,
        tipo: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
   
        resultados = []

        # Query para editais
        query_editais = {}
        if status:
            query_editais['status'] = status.capitalize()
        if area:
            query_editais['areas'] = {'$regex': area, '$options': 'i'}
        if tipo and tipo in ['edital', 'bolsa']:
            query_editais['tipo'] = tipo

        try:
            editais = list(self.db['editais'].find(query_editais).limit(limit))
            for edital in editais:
                edital['_id'] = str(edital['_id'])
                resultados.append(edital)
        except Exception as e:
            logger.error(f"Erro ao buscar editais: {str(e)}")

        # Query para vagas (se não houver filtro de tipo específico para editais)
        if not tipo or tipo in ['vaga', 'estagio']:
            query_vagas = {}
            if area:
                query_vagas['area'] = {'$regex': area, '$options': 'i'}

            try:
                vagas = list(self.db['vagas'].find(query_vagas).limit(limit))
                for vaga in vagas:
                    vaga['_id'] = str(vaga['_id'])
                    resultados.append(vaga)
            except Exception as e:
                logger.error(f"Erro ao buscar vagas: {str(e)}")

        logger.info(f"Encontradas {len(resultados)} oportunidades")
        return resultados

    def get_editais(
        self,
        status: Optional[str] = None,
        fonte: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
     
        query = {}
        if status:
            query['status'] = status.capitalize()
        if fonte:
            query['fonte'] = {'$regex': fonte, '$options': 'i'}

        try:
            editais = list(self.db['editais'].find(query).limit(limit))
            for edital in editais:
                edital['_id'] = str(edital['_id'])
            logger.info(f"Encontrados {len(editais)} editais")
            return editais
        except Exception as e:
            logger.error(f"Erro ao buscar editais: {str(e)}")
            return []

    def get_vagas(
        self,
        area: Optional[str] = None,
        fonte: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
     
        query = {}
        if area:
            query['area'] = {'$regex': area, '$options': 'i'}
        if fonte:
            query['fonte'] = {'$regex': fonte, '$options': 'i'}

        try:
            vagas = list(self.db['vagas'].find(query).limit(limit))
            for vaga in vagas:
                vaga['_id'] = str(vaga['_id'])
            logger.info(f"Encontradas {len(vagas)} vagas")
            return vagas
        except Exception as e:
            logger.error(f"Erro ao buscar vagas: {str(e)}")
            return []

    def get_noticias(
        self,
        categoria: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
      
        query = {}
        if categoria:
            query['categoria'] = {'$regex': categoria, '$options': 'i'}

        try:
            noticias = list(self.db['noticias'].find(query).limit(limit))
            for noticia in noticias:
                noticia['_id'] = str(noticia['_id'])
            logger.info(f"Encontradas {len(noticias)} notícias")
            return noticias
        except Exception as e:
            logger.error(f"Erro ao buscar notícias: {str(e)}")
            return []

    def get_by_id(self, doc_id: str, collection: str = 'editais') -> Optional[Dict[str, Any]]:
   
        try:
            from bson import ObjectId
            doc = self.db[collection].find_one({'_id': ObjectId(doc_id)})
            if doc:
                doc['_id'] = str(doc['_id'])
            return doc
        except Exception as e:
            logger.error(f"Erro ao buscar documento por ID: {str(e)}")
            return None

    def update_status(self) -> int:
        """
        Atualiza o status de todos os editais baseado na data limite

        Returns:
            Número de documentos atualizados
        """
        from datetime import datetime
        hoje = datetime.now()

        try:
            # Marca como Encerrado os editais com data_limite < hoje
            result_encerrados = self.db['editais'].update_many(
                {
                    'data_limite': {'$lt': hoje.strftime('%d/%m/%Y')},
                    'status': {'$ne': 'Encerrado'}
                },
                {'$set': {'status': 'Encerrado'}}
            )

            # Marca como Aberto os editais com data_limite >= hoje
            result_abertos = self.db['editais'].update_many(
                {
                    'data_limite': {'$gte': hoje.strftime('%d/%m/%Y')},
                    'status': {'$ne': 'Aberto'}
                },
                {'$set': {'status': 'Aberto'}}
            )

            total = result_encerrados.modified_count + result_abertos.modified_count
            logger.info(f"Status atualizados: {total} documentos")
            return total
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")
            return 0

    def close(self) -> None:
        """Fecha a conexão com MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Conexão com MongoDB fechada")
