from abc import ABC, abstractmethod
import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

class BaseScraper(ABC):
    """
    Classe base abstrata para todos os robôs de coleta da plataforma EduScrap.
    Atende ao RNF05 e à arquitetura de classes UML (Figura 11).
    Garante que novas fontes não exijam alterações no núcleo do sistema.
    """
    def __init__(self, nome_fonte: str, url_base: str, nome_colecao: str = "oportunidades"):
        self.nome_fonte: str = nome_fonte
        self.url_base: str = url_base
        self.nome_colecao: str = nome_colecao
        self.logger: logging.Logger = logging.getLogger(f"scraper.{self.nome_fonte.lower()}")
        
        self.mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.mongodb_db: str = os.getenv("MONGODB_DB", "hub_estudantes")
        self._client: Optional[MongoClient] = None

    @property
    def db(self):
        if self._client is None:
            self._client = MongoClient(self.mongodb_uri)
        return self._client[self.mongodb_db]

    @property
    def colecao(self):
        return self.db[self.nome_colecao]

    @abstractmethod
    def coletar(self) -> List[Dict[str, Any]]:
        """
        Método abstrato que deve ser implementado por cada scraper concreto.
        Executa a extração dos dados da fonte oficial e retorna lista de dicionários.
        """
        pass

    def salvar_no_banco(self, oportunidades: List[Dict[str, Any]]) -> int:
        """
        Persiste as oportunidades extraídas no MongoDB com upsert pelo link canônico (RN04).
        Retorna o total de registros salvos ou atualizados.
        """
        if not oportunidades:
            self.logger.info(f"[{self.nome_fonte}] Nenhuma oportunidade para salvar.")
            return 0

        salvos = 0
        for item in oportunidades:
            link = item.get("link") or item.get("url")
            if not link:
                continue

            # Garante campos padronizados
            item["fonte"] = self.nome_fonte
            item["coletado_em"] = datetime.now()
            
            try:
                self.colecao.update_one(
                    {"link": link},
                    {"$set": item},
                    upsert=True
                )
                salvos += 1
            except Exception as e:
                self.logger.error(f"Erro ao salvar oportunidade '{link}': {e}")

        self.logger.info(f"[{self.nome_fonte}] {salvos} oportunidades persistidas na coleção '{self.nome_colecao}'.")
        return salvos

    def limpar_texto(self, texto: Optional[str]) -> str:
        """
        Remove espaços excessivos, quebras de linha e caracteres de controle de strings extraídas.
        """
        if not texto:
            return ""
        texto_limpo = re.sub(r"\s+", " ", str(texto)).strip()
        return texto_limpo

    def executar(self) -> int:
        """
        Fluxo template padrão de execução: coletar -> salvar_no_banco.
        """
        self.logger.info(f"=== Iniciando coleta: {self.nome_fonte} ({self.url_base}) ===")
        inicio = datetime.now()
        try:
            dados = self.coletar()
            total = self.salvar_no_banco(dados)
            duracao = (datetime.now() - inicio).total_seconds()
            self.logger.info(f"=== Concluída coleta: {self.nome_fonte} | {total} itens | {duracao:.2f}s ===")
            return total
        except Exception as e:
            self.logger.error(f"Falha na coleta de {self.nome_fonte}: {e}", exc_info=True)
            return 0
