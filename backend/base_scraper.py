from abc import ABC, abstractmethod
import atexit
import os
import re
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient

# Garante saída UTF-8 sem buffer no Windows e Linux para evitar UnicodeEncodeError e logs truncados
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace", write_through=True)
        except Exception:
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

_LOGGERS_CONFIGURADOS = set()


def configurar_log_scraper(
    chave_log: str,
    nome_fonte: str,
    colecao_nome: str,
    filtro_contagem: Optional[Dict[str, Any]] = None,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """
    Configura logging padronizado para um scraper (execução direta ou via run_scrapers.py).
    Quando executado diretamente (sem EDUSCRAP_RUNNER=1), grava automaticamente em
    logs/<chave_log>.log com o cabeçalho e o rodapé esperados por _parsear_arquivo_log.
    """
    logger = logging.getLogger(logger_name or f"scraper_{chave_log}")
    if chave_log in _LOGGERS_CONFIGURADOS:
        return logger
    _LOGGERS_CONFIGURADOS.add(chave_log)

    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    # Se não estiver rodando dentro do run_scrapers.py, anexa FileHandler direto para logs/<chave_log>.log
    if os.getenv("EDUSCRAP_RUNNER") != "1":
        project_root = Path(__file__).resolve().parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_file_path = logs_dir / f"{chave_log}.log"
        inicio = time.time()

        try:
            with open(log_file_path, "w", encoding="utf-8") as f_hdr:
                f_hdr.write(f"=== INÍCIO DA VARREDURA: {nome_fonte} ===\n")
                f_hdr.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_hdr.write(f"Comando: {sys.executable} {Path(sys.argv[0]).name}\n\n")

            fh = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
            fh.setFormatter(fmt)
            root_logger.addHandler(fh)

            def _escrever_rodape():
                duracao = round(time.time() - inicio, 1)
                itens = 0
                try:
                    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
                    db_name = os.getenv("MONGODB_DB", "hub_estudantes")
                    client = MongoClient(uri, serverSelectionTimeoutMS=800)
                    itens = client[db_name][colecao_nome].count_documents(filtro_contagem or {})
                    client.close()
                except Exception:
                    pass
                try:
                    logger.info(f"Concluído em {duracao}s! (Itens na base: {itens})")
                    fh.flush()
                except Exception:
                    pass

            atexit.register(_escrever_rodape)
        except Exception as e:
            logger.warning(f"Não foi possível inicializar arquivo de log {log_file_path}: {e}")

    return logger


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
