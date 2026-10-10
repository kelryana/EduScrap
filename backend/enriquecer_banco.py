# backend/enriquecer_banco.py

import os
import sys
import logging
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.normalizer.classifier import classificar_oportunidade

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("enriquecer_banco")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")


def enriquecer_todas_as_colecoes():
    logger.info("Conectando ao MongoDB para enriquecimento semântico...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    colecoes_alvo = [
        "editais", "vagas", "noticias",
        "vagas_estagio", "vagas_bolsa", "vagas_ufersa",
        "vagas_portal_uern", "vagas_ciee"
    ]

    total_atualizados = 0

    for col_name in colecoes_alvo:
        if col_name not in db.list_collection_names():
            continue

        col = db[col_name]
        docs = list(col.find({}))
        logger.info(f"Processando coleção '{col_name}' com {len(docs)} documentos...")

        modificados = 0
        for doc in docs:
            titulo = doc.get("titulo") or doc.get("nome") or doc.get("nome_completo") or ""
            descricao = doc.get("descricao") or doc.get("resumo") or doc.get("categoria") or ""

            classificacao = classificar_oportunidade(titulo, descricao)
            cursos = classificacao["cursos"]
            areas = classificacao["areas"]

            # Fallbacks semânticos baseados na categoria / fonte da coleção
            if not areas:
                if "bolsa" in col_name or "proex" in col_name:
                    areas = ["Extensão", "Pesquisa"]
                elif "estagio" in col_name or "ciee" in col_name:
                    areas = ["Mercado", "Estágio"]
                elif "ufersa" in col_name:
                    areas = ["Assistência Estudantil", "Universitário"]
                else:
                    areas = ["Geral / Universitário"]

            update_fields = {
                "cursos": cursos,
                "areas": areas,
                "geral": classificacao["geral"]
            }

            # Garante que titulo e status existam de forma unificada
            if not doc.get("titulo") and titulo:
                update_fields["titulo"] = titulo
            if not doc.get("status"):
                update_fields["status"] = "Aberto"

            col.update_one(
                {"_id": doc["_id"]},
                {"$set": update_fields}
            )
            modificados += 1

        logger.info(f"-> Coleção '{col_name}': {modificados} documentos atualizados com sucesso.")
        total_atualizados += modificados

    logger.info(f"Concluído! Total de {total_atualizados} oportunidades enriquecidas com cursos e áreas.")
    client.close()


if __name__ == "__main__":
    enriquecer_todas_as_colecoes()
