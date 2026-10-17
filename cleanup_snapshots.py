#!/usr/bin/env python3
"""
EduScrap - Script de Retenção de Snapshots (Item 16)
Remove arquivos e snapshots de PDFs armazenados no GridFS do MongoDB há mais de 12 meses (365 dias).
Protege o armazenamento SSD contra crescimento indefinido.
Executável manualmente ou via systemd timer (eduscrap-cleanup.timer).
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Carrega ambiente
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("cleanup_snapshots")


def limpar_snapshots_antigos(dias_retencao: int = 365, uri: str = None, db_name: str = None) -> dict:
    """
    Remove arquivos do GridFS cuja data de upload/criação seja anterior a `dias_retencao`.
    Retorna métricas de limpeza: {apagados, bytes_liberados, total_analisados}.
    """
    try:
        from pymongo import MongoClient
        import gridfs
    except ImportError as e:
        logger.error(f"Dependências ausentes (pymongo/gridfs): {e}")
        return {"sucesso": False, "erro": str(e), "apagados": 0, "bytes_liberados": 0}

    uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = db_name or os.getenv("MONGODB_DB", "hub_estudantes")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        db = client[db_name]
        fs = gridfs.GridFS(db)
    except Exception as e:
        logger.error(f"Falha de conexão com o MongoDB: {e}")
        return {"sucesso": False, "erro": str(e), "apagados": 0, "bytes_liberados": 0}

    data_corte = datetime.now() - timedelta(days=dias_retencao)
    logger.info(f"Iniciando política de retenção ({dias_retencao} dias). Data limite de corte: {data_corte.strftime('%Y-%m-%d %H:%M:%S')}")

    filtro_expirados = {
        "$or": [
            {"uploadDate": {"$lt": data_corte}},
            {"data_captura": {"$lt": data_corte}}
        ]
    }

    apagados = 0
    bytes_liberados = 0
    total_analisados = 0

    try:
        colecao_files = db["fs.files"]
        arquivos_expirados = list(colecao_files.find(filtro_expirados))
        total_analisados = len(arquivos_expirados)

        for doc in arquivos_expirados:
            file_id = doc["_id"]
            tamanho = doc.get("length", 0)
            nome = doc.get("filename", "sem_nome")
            try:
                fs.delete(file_id)
                apagados += 1
                bytes_liberados += tamanho
                logger.debug(f"Snapshot removido: {nome} (ID: {file_id}, {tamanho} bytes)")
            except Exception as ex_del:
                logger.warning(f"Erro ao deletar snapshot {file_id}: {ex_del}")

        mb_liberados = round(bytes_liberados / (1024 * 1024), 2)
        logger.info(
            f"Limpeza de retenção concluída com sucesso! "
            f"Snapshots apagados: {apagados}/{total_analisados} | "
            f"Espaço liberado: {mb_liberados} MB"
        )

        return {
            "sucesso": True,
            "apagados": apagados,
            "total_analisados": total_analisados,
            "bytes_liberados": bytes_liberados,
            "mb_liberados": mb_liberados,
            "data_corte": str(data_corte)
        }

    except Exception as e:
        logger.error(f"Erro durante execução da rotina de retenção: {e}", exc_info=True)
        return {
            "sucesso": False,
            "erro": str(e),
            "apagados": apagados,
            "bytes_liberados": bytes_liberados
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Limpeza e retenção de snapshots GridFS (EduScrap)")
    parser.add_argument("--dias", type=int, default=365, help="Dias de retenção (padrão: 365 / 12 meses)")
    args = parser.parse_args()

    res = limpar_snapshots_antigos(dias_retencao=args.dias)
    if res.get("sucesso"):
        print(f"Sucesso: {res['apagados']} snapshots apagados, {res.get('mb_liberados', 0)} MB liberados.")
        sys.exit(0)
    else:
        print(f"Erro na limpeza: {res.get('erro')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
