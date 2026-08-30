#src/normalizer/json_builder.py 

from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONBuilder:
      def __init__(self):
        """Inicializa o construtor"""
        self.schema_version = "1.0"
    def build_edital(
        self,
        titulo: str,
        fonte: str,
        url: str,
        data_publicacao: str,
        data_limite: Optional[str] = None,
        edital_numero: Optional[str] = None,
        valor: Optional[str] = None,
        areas: Optional[List[str]] = None,
        raw_text: Optional[str] = None,
        status: str = "Aberto",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Constrói documento JSON para edital

        Args:
            titulo: Título do edital
            fonte: Fonte de origem (UERN, UFERSA, JOUERN, etc.)
            url: URL original do edital
            data_publicacao: Data de publicação
            data_limite: Data limite para inscrições
            edital_numero: Número do edital
            valor: Valor da bolsa/auxílio
            areas: Lista de áreas de conhecimento
            raw_text: Texto bruto extraído
            status: Status atual (Aberto/Encerrado)
            metadata: Metadados adicionais

        Returns:
            Documento JSON padronizado
        """
        document = {
            "tipo": "edital",
            "titulo": titulo,
            "fonte": fonte,
            "url": url,
            "data_publicacao": data_publicacao,
            "data_limite": data_limite,
            "edital_numero": edital_numero,
            "valor": valor,
            "areas": areas or [],
            "status": status,
            "raw_text": raw_text,
            "metadata": metadata or {},
            "schema_version": self.schema_version,
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": datetime.now().isoformat()
        }

        logger.info(f"Documento edital construído: {titulo[:50]}...")
        return document
    def build_vaga_estagio(
        self,
        titulo: str,
        fonte: str,
        url: str,
        empresa: str,
        area: str,
        descricao: Optional[str] = None,
        requisitos: Optional[List[str]] = None,
        beneficios: Optional[List[str]] = None,
        salario: Optional[str] = None,
        carga_horaria: Optional[str] = None,
        local: Optional[str] = None,
        data_publicacao: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constrói documento JSON para vaga de estágio

        Args:
            titulo: Título da vaga
            fonte: Fonte de origem (CIEE, etc.)
            url: URL original da vaga
            empresa: Nome da empresa
            area: Área de atuação
            descricao: Descrição da vaga
            requisitos: Lista de requisitos
            beneficios: Lista de benefícios
            salario: Faixa salarial
            carga_horaria: Carga horária
            local: Local de trabalho
            data_publicacao: Data de publicação
            raw_text: Texto bruto extraído

        Returns:
            Documento JSON padronizado
        """
        document = {
            "tipo": "vaga_estagio",
            "titulo": titulo,
            "fonte": fonte,
            "url": url,
            "empresa": empresa,
            "area": area,
            "descricao": descricao,
            "requisitos": requisitos or [],
            "beneficios": beneficios or [],
            "salario": salario,
            "carga_horaria": carga_horaria,
            "local": local,
            "data_publicacao": data_publicacao or datetime.now().strftime('%d/%m/%Y'),
            "status": "Aberto",  # Vagas de estágio geralmente não têm data fixa
            "raw_text": raw_text,
            "schema_version": self.schema_version,
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": datetime.now().isoformat()
        }

        logger.info(f"Documento vaga construído: {titulo[:50]}...")
        return document
    def build_noticia(
        self,
        titulo: str,
        fonte: str,
        url: str,
        conteudo: str,
        categoria: str,
        tags: Optional[List[str]] = None,
        autor: Optional[str] = None,
        data_publicacao: Optional[str] = None,
        imagem_url: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constrói documento JSON para notícia

        Args:
            titulo: Título da notícia
            fonte: Fonte de origem
            url: URL original
            conteudo: Conteúdo da notícia
            categoria: Categoria (Tecnologia, Saúde, etc.)
            tags: Tags relacionadas
            autor: Autor da matéria
            data_publicacao: Data de publicação
            imagem_url: URL da imagem principal
            raw_text: Texto bruto extraído

        Returns:
            Documento JSON padronizado
        """
        document = {
            "tipo": "noticia",
            "titulo": titulo,
            "fonte": fonte,
            "url": url,
            "conteudo": conteudo,
            "categoria": categoria,
            "tags": tags or [],
            "autor": autor,
            "data_publicacao": data_publicacao or datetime.now().strftime('%d/%m/%Y'),
            "imagem_url": imagem_url,
            "raw_text": raw_text,
            "schema_version": self.schema_version,
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": datetime.now().isoformat()
        }

        logger.info(f"Documento notícia construído: {titulo[:50]}...")
        return document
    def to_json(self, document: Dict, pretty: bool = True) -> str:
    
        indent = 2 if pretty else None
        return json.dumps(document, ensure_ascii=False, indent=indent)
    def from_json(self, json_str: str) -> Dict:
      
        return json.loads(json_str)
    def validate_schema(self, document: Dict) -> bool:
    
        required_fields = ['tipo', 'titulo', 'fonte', 'url']

        for field in required_fields:
            if field not in document:
                logger.error(f"Campo obrigatório faltando: {field}")
                return False

        if document.get('schema_version') != self.schema_version:
            logger.warning(f"Versão do schema incompatível: {document.get('schema_version')}")

        return True
