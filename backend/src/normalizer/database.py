# src/normalizer/database.py

from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBHandler:
    def __init__(self, uri: str = None, db_name: str = "hub_estudantes", client=None):
      
        self.uri = uri or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = db_name
        self.client = client
        self.db = None
        if self.client is not None:
            self.db = self.client[self.db_name]
            logger.info(f"MongoDBHandler usando cliente injetado: {self.db_name}")
        else:
            self._connect()

    def _connect(self) -> None:
       
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

            # Coleção de usuários
            usuarios = self.db['usuarios']
            usuarios.create_index([("email", ASCENDING)], unique=True, name="idx_usuario_email")
            usuarios.create_index([("matricula", ASCENDING)], sparse=True, name="idx_usuario_matricula")

            logger.info("Índices criados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar índices: {str(e)}")

    def insert_edital(self, edital_data: Dict[str, Any]) -> Optional[str]:
    
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

    def insert_vaga(self, vaga_data: Dict[str, Any]) -> Optional[str]:
     
        try:
            vaga_data['atualizado_em'] = datetime.now().isoformat()
            result = self.db['vagas'].insert_one(vaga_data)
            logger.info(f"Vaga inserida com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir vaga: {str(e)}")
            return None

    def insert_noticia(self, noticia_data: Dict[str, Any]) -> Optional[str]:
     
        try:
            noticia_data['atualizado_em'] = datetime.now().isoformat()
            result = self.db['noticias'].insert_one(noticia_data)
            logger.info(f"Notícia inserida com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao inserir notícia: {str(e)}")
            return None

    def upsert_documento(self, doc: Dict[str, Any], collection_name: str, identifier_field: str) -> Optional[str]:
    
        try:
            # Adiciona timestamp de atualização
            doc['atualizado_em'] = datetime.now().isoformat()
            
            # Define o filtro para encontrar documento existente
            filter_criteria = {identifier_field: doc[identifier_field]}
            
            # Realiza upsert
            result = self.db[collection_name].replace_one(
                filter_criteria,
                doc,
                upsert=True
            )
            
            # Se foi um insert, obtemos o ID do documento recém-inserido
            if result.upserted_id:
                logger.info(f"Documento inserido com ID: {result.upserted_id}")
                return str(result.upserted_id)
            else:
                # Se foi um update, precisamos buscar o ID do documento
                found_doc = self.db[collection_name].find_one(filter_criteria)
                if found_doc:
                    doc_id = str(found_doc['_id'])
                    logger.info(f"Documento atualizado com ID: {doc_id}")
                    return doc_id
                else:
                    # Caso raro: documento não encontrado após replace_one
                    logger.warning(f"Documento não encontrado após upsert: {filter_criteria}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao realizar upsert: {str(e)}")
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

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
       
        try:
            # Normaliza email
            if 'email' in user_data:
                user_data['email'] = user_data['email'].strip().lower()

            # Verifica se já existe usuário com esse email
            if self.db['usuarios'].find_one({'email': user_data['email']}):
                logger.warning(f"Usuário com email {user_data['email']} já existe")
                return None

            user_data.setdefault('matricula', '')
            user_data.setdefault('preferencias', {
                'cursos': [],
                'areas': [],
                'receber_emails': True
            })
            user_data.setdefault('favoritos', [])
            user_data['criado_em'] = datetime.now().isoformat()
            user_data['atualizado_em'] = datetime.now().isoformat()

            result = self.db['usuarios'].insert_one(user_data)
            logger.info(f"Usuário criado com ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Erro ao criar usuário: {str(e)}")
            return None

    def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        
        try:
            if not email:
                return None
            user = self.db['usuarios'].find_one({'email': email.strip().lower()})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por email: {str(e)}")
            return None

    def find_user_by_id(self, user_id: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
       
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(user_id)
            except Exception:
                oid = user_id

            user = self.db['usuarios'].find_one({'_id': oid})
            if user:
                user['_id'] = str(user['_id'])
                if not include_password and 'senha_hash' in user:
                    del user['senha_hash']
            return user
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID: {str(e)}")
            return None

    def update_user_preferences(self, user_id: str, preferencias: Dict[str, Any]) -> bool:
       
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(user_id)
            except Exception:
                oid = user_id

            update_data = {}
            if 'cursos' in preferencias:
                update_data['preferencias.cursos'] = preferencias['cursos']
            if 'areas' in preferencias:
                update_data['preferencias.areas'] = preferencias['areas']
            if 'receber_emails' in preferencias:
                update_data['preferencias.receber_emails'] = bool(preferencias['receber_emails'])

            update_data['atualizado_em'] = datetime.now().isoformat()

            result = self.db['usuarios'].update_one(
                {'_id': oid},
                {'$set': update_data}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            logger.error(f"Erro ao atualizar preferências do usuário: {str(e)}")
            return False

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
      
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(user_id)
            except Exception:
                oid = user_id

            allowed_fields = ['nome', 'matricula']
            update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
            update_data['atualizado_em'] = datetime.now().isoformat()

            result = self.db['usuarios'].update_one(
                {'_id': oid},
                {'$set': update_data}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            logger.error(f"Erro ao atualizar perfil do usuário: {str(e)}")
            return False

    def add_favorito(self, user_id: str, oportunidade_id: str) -> bool:
       
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(user_id)
            except Exception:
                oid = user_id

            result = self.db['usuarios'].update_one(
                {'_id': oid},
                {
                    '$addToSet': {'favoritos': str(oportunidade_id)},
                    '$set': {'atualizado_em': datetime.now().isoformat()}
                }
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Erro ao adicionar favorito: {str(e)}")
            return False

    def remove_favorito(self, user_id: str, oportunidade_id: str) -> bool:
        
        try:
            from bson import ObjectId
            try:
                oid = ObjectId(user_id)
            except Exception:
                oid = user_id

            result = self.db['usuarios'].update_one(
                {'_id': oid},
                {
                    '$pull': {'favoritos': str(oportunidade_id)},
                    '$set': {'atualizado_em': datetime.now().isoformat()}
                }
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Erro ao remover favorito: {str(e)}")
            return False

    def get_user_favoritos(self, user_id: str) -> List[Dict[str, Any]]:
       
        try:
            user = self.find_user_by_id(user_id)
            if not user or not user.get('favoritos'):
                return []

            fav_ids = user.get('favoritos', [])
            favoritos = []

            for fav_id in fav_ids:
                # Busca em editais e vagas
                item = self.get_by_id(fav_id, collection='editais')
                if item:
                    item['tipo_documento'] = 'edital'
                    item['favorito'] = True
                    favoritos.append(item)
                    continue

                item = self.get_by_id(fav_id, collection='vagas')
                if item:
                    item['tipo_documento'] = 'vaga'
                    item['favorito'] = True
                    favoritos.append(item)
                    continue

                item = self.get_by_id(fav_id, collection='noticias')
                if item:
                    item['tipo_documento'] = 'noticia'
                    item['favorito'] = True
                    favoritos.append(item)

            return favoritos
        except Exception as e:
            logger.error(f"Erro ao buscar favoritos do usuário: {str(e)}")
            return []

    def get_feed_personalizado(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
       
        try:
            user = self.find_user_by_id(user_id)
            if not user:
                return self.get_oportunidades(limit=limit)

            preferencias = user.get('preferencias', {})
            cursos = preferencias.get('cursos', [])
            areas = preferencias.get('areas', [])
            user_favoritos = set(user.get('favoritos', []))

            # Se não houver cursos ou áreas selecionados, retorna oportunidades gerais vigentes
            if not cursos and not areas:
                todas = self.get_oportunidades(status="Aberto", limit=limit)
                for item in todas:
                    item['favorito'] = item.get('_id') in user_favoritos
                return todas

            # Monta critérios de busca inteligente
            criterios_or = []

            if cursos:
                criterios_or.append({'cursos': {'$in': cursos}})
                for c in cursos:
                    criterios_or.append({'titulo': {'$regex': re.escape(c), '$options': 'i'}})
                    criterios_or.append({'descricao': {'$regex': re.escape(c), '$options': 'i'}})

            if areas:
                criterios_or.append({'areas': {'$in': areas}})
                for a in areas:
                    criterios_or.append({'areas': {'$regex': re.escape(a), '$options': 'i'}})
                    criterios_or.append({'area': {'$regex': re.escape(a), '$options': 'i'}})
                    criterios_or.append({'titulo': {'$regex': re.escape(a), '$options': 'i'}})

            if not criterios_or:
                todas = self.get_oportunidades(status="Aberto", limit=limit)
                for item in todas:
                    item['favorito'] = item.get('_id') in user_favoritos
                return todas

            query_filtro = {'$or': criterios_or}
            resultados = []
            ids_vistos = set()

            # 1. Busca em Editais (CPPS, PRAE, PROEX, UERN, etc.)
            try:
                editais = list(self.db['editais'].find(query_filtro).limit(limit))
                for edital in editais:
                    ed_id = str(edital['_id'])
                    if ed_id not in ids_vistos:
                        ids_vistos.add(ed_id)
                        edital['_id'] = ed_id
                        edital['tipo_documento'] = 'edital'
                        edital['favorito'] = ed_id in user_favoritos
                        resultados.append(edital)
            except Exception as e_ed:
                logger.warning(f"Erro ao buscar editais personalizados: {e_ed}")

            # 2. Busca em Vagas (MPRN, CIEE, Estágios)
            try:
                vagas = list(self.db['vagas'].find(query_filtro).limit(limit))
                for vaga in vagas:
                    vg_id = str(vaga['_id'])
                    if vg_id not in ids_vistos:
                        ids_vistos.add(vg_id)
                        vaga['_id'] = vg_id
                        vaga['tipo_documento'] = 'vaga'
                        vaga['favorito'] = vg_id in user_favoritos
                        resultados.append(vaga)
            except Exception as e_vg:
                logger.warning(f"Erro ao buscar vagas personalizadas: {e_vg}")

            # 3. Busca em Notícias Acadêmicas (ASSECOM UFERSA, Comunicados)
            try:
                noticias = list(self.db['noticias'].find(query_filtro).limit(limit))
                for notic in noticias:
                    nt_id = str(notic['_id'])
                    if nt_id not in ids_vistos:
                        ids_vistos.add(nt_id)
                        notic['_id'] = nt_id
                        notic['tipo_documento'] = 'noticia'
                        notic['favorito'] = nt_id in user_favoritos
                        resultados.append(notic)
            except Exception as e_nt:
                logger.warning(f"Erro ao buscar notícias personalizadas: {e_nt}")

            # Ordena com base no grau de relevância (se bate curso primeiro, depois área)
            def score_relevancia(item):
                score = 0
                item_cursos = item.get('cursos', []) or []
                item_areas = item.get('areas', []) or []
                item_titulo = item.get('titulo', '')

                # Bate curso específico selecionado
                for c in cursos:
                    if c in item_cursos or re.search(re.escape(c), item_titulo, re.IGNORECASE):
                        score += 10

                # Bate área selecionada
                for a in areas:
                    if a in item_areas or re.search(re.escape(a), item_titulo, re.IGNORECASE):
                        score += 4

                return score

            resultados.sort(key=score_relevancia, reverse=True)

            # Se encontrou resultados relevantes, retorna a lista enriquecida
            if resultados:
                return resultados[:limit]

            # Fallback seguro apenas se não encontrar absolutamente nada
            gerais = self.get_oportunidades(status="Aberto", limit=limit)
            for item in gerais:
                item['favorito'] = item.get('_id') in user_favoritos
            return gerais
        except Exception as e:
            logger.error(f"Erro ao buscar feed personalizado: {str(e)}")
            return self.get_oportunidades(limit=limit)

    def close(self) -> None:
       
        if self.client:
            self.client.close()
            logger.info("Conexão com MongoDB fechada")
