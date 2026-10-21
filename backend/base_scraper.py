from abc import ABC, abstractmethod
import atexit
import os
import re
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING

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

DIAS_TOLERANCIA_VENCIDOS = 10
COLECOES_OPORTUNIDADES = (
    "vagas_estagio",
    "vagas_bolsa",
    "vagas_ufersa",
    "vagas_ciee",
    "vagas_portal_uern",
    "vagas",
    "editais",
    "noticias",
    "vagas_noticias",
    "oportunidades",
)


def _normalizar_datetime(valor: Any) -> Optional[datetime]:
    """Converte datetime ou string (ISO / DD/MM/YYYY) em objeto datetime."""
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, str) and valor.strip():
        texto = valor.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(texto[:19], fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(texto.replace("Z", ""))
        except Exception:
            return None
    return None


def eh_vencido_alem_do_limite(
    data_vencimento: Any,
    dias: int = DIAS_TOLERANCIA_VENCIDOS,
    referencia: Optional[datetime] = None,
) -> bool:
    """
    Retorna True se data_vencimento já estiver vencida há mais de `dias` dias
    (padrão: 10 dias).
    """
    dt = _normalizar_datetime(data_vencimento)
    if dt is None:
        return False
    agora = referencia or datetime.now()
    data_corte = agora - timedelta(days=dias)
    return dt < data_corte


def obter_prazo_cacheado(
    db: Any,
    link: Optional[str] = None,
    nome: Optional[str] = None,
    colecao_atual: Optional[Any] = None,
) -> Optional[datetime]:
    """
    Recupera `data_vencimento` já conhecida para um link ou nome (seja na própria
    coleção ativa ou no cache `cache_prazos_pdf`), evitando re-download de PDFs
    antigos que já foram expurgados por terem mais de 10 dias de vencidos.
    """
    try:
        if colecao_atual is not None:
            filtro_col = {"link": link} if link else ({"nome": nome} if nome else None)
            if filtro_col:
                doc = colecao_atual.find_one(filtro_col, {"data_vencimento": 1})
                if doc and doc.get("data_vencimento"):
                    return _normalizar_datetime(doc.get("data_vencimento"))

        if db is not None:
            cache_col = db["cache_prazos_pdf"]
            if link:
                reg = cache_col.find_one({"link": link}, {"data_vencimento": 1})
                if reg and reg.get("data_vencimento"):
                    return _normalizar_datetime(reg.get("data_vencimento"))
            if nome:
                reg = cache_col.find_one({"nome": nome}, {"data_vencimento": 1})
                if reg and reg.get("data_vencimento"):
                    return _normalizar_datetime(reg.get("data_vencimento"))
    except Exception:
        pass
    return None


def salvar_prazo_cacheado(
    db: Any,
    link: Optional[str],
    nome: Optional[str],
    data_vencimento: Any,
) -> None:
    """Persiste o prazo extraído em `cache_prazos_pdf` para evitar re-download de PDFs."""
    dt = _normalizar_datetime(data_vencimento)
    if db is None or dt is None or (not link and not nome):
        return
    try:
        chave = {"link": link} if link else {"nome": nome}
        db["cache_prazos_pdf"].update_one(
            chave,
            {
                "$set": {
                    "link": link or "",
                    "nome": nome or "",
                    "data_vencimento": dt,
                    "atualizado_em": datetime.now(),
                }
            },
            upsert=True,
        )
    except Exception:
        pass


def limpar_itens_vencidos_banco(
    db: Any = None,
    dias: int = DIAS_TOLERANCIA_VENCIDOS,
) -> int:
    """
    Remove automaticamente do MongoDB todos os itens cuja `data_vencimento` (ou `data_limite`)
    tenha ultrapassado mais de `dias` dias (padrão: 10 dias de vencido).
    Antes da exclusão, registra o prazo em `cache_prazos_pdf` para que os scrapers não
    precisem baixar novamente PDFs antigos já descartados.
    """
    fechar_cliente = False
    client = None
    try:
        if db is None:
            uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            db_name = os.getenv("MONGODB_DB", "hub_estudantes")
            client = MongoClient(uri, serverSelectionTimeoutMS=1500)
            db = client[db_name]
            fechar_cliente = True

        agora = datetime.now()
        data_corte = agora - timedelta(days=dias)
        total_removidos = 0
        colecoes_existentes = set(db.list_collection_names())

        query_vencidos = {
            "$or": [
                {"data_vencimento": {"$lt": data_corte}},
                {"data_limite": {"$lt": data_corte}},
            ]
        }

        for nome_col in COLECOES_OPORTUNIDADES:
            if nome_col not in colecoes_existentes:
                continue
            col = db[nome_col]
            try:
                # Salva no cache leve os prazos dos itens que serão expurgados
                for doc in col.find(
                    query_vencidos,
                    {"link": 1, "url": 1, "nome": 1, "titulo": 1, "data_vencimento": 1, "data_limite": 1},
                ):
                    salvar_prazo_cacheado(
                        db,
                        doc.get("link") or doc.get("url"),
                        doc.get("nome") or doc.get("titulo"),
                        doc.get("data_vencimento") or doc.get("data_limite"),
                    )

                res = col.delete_many(query_vencidos)
                total_removidos += res.deleted_count

                # Também verifica eventuais datas salvas como string
                ids_str_vencidos = []
                for doc in col.find(
                    {"data_vencimento": {"$type": "string"}},
                    {"_id": 1, "link": 1, "nome": 1, "titulo": 1, "data_vencimento": 1},
                ):
                    dt_parsed = _normalizar_datetime(doc.get("data_vencimento"))
                    if dt_parsed and dt_parsed < data_corte:
                        salvar_prazo_cacheado(
                            db,
                            doc.get("link"),
                            doc.get("nome") or doc.get("titulo"),
                            dt_parsed,
                        )
                        ids_str_vencidos.append(doc["_id"])
                if ids_str_vencidos:
                    res_str = col.delete_many({"_id": {"$in": ids_str_vencidos}})
                    total_removidos += res_str.deleted_count

                # Garante índice TTL nativo no MongoDB (expira 10 dias após data_vencimento)
                try:
                    col.create_index(
                        [("data_vencimento", ASCENDING)],
                        expireAfterSeconds=dias * 86400,
                        name="idx_ttl_data_vencimento_10d",
                    )
                except Exception:
                    pass
            except Exception:
                continue

        return total_removidos
    except Exception:
        return 0
    finally:
        if fechar_cliente and client is not None:
            try:
                client.close()
            except Exception:
                pass


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
                    limpar_itens_vencidos_banco(client[db_name])
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

            dt_venc = item.get("data_vencimento") or item.get("data_limite")
            if dt_venc:
                salvar_prazo_cacheado(self.db, link, item.get("nome") or item.get("titulo"), dt_venc)
                if eh_vencido_alem_do_limite(dt_venc):
                    try:
                        self.colecao.delete_one({"link": link})
                    except Exception:
                        pass
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

        limpar_itens_vencidos_banco(self.db)
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
