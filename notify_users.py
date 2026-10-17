#!/usr/bin/env python3
"""
EduScrap - Notificador de Prazos Críticos de Editais (Item 7)
Script autônomo que consulta o MongoDB, identifica editais com encerramento em até 3 dias (≤ 3 dias),
localiza usuários que favoritaram o certame e envia alertas multicanal:
1. E-mail (via SMTP)
2. Notificação Webhook Telegram (via Bot API)

Projetado para consumir menos de 100 MB de RAM por execução e encerrar.
Orquestrado via systemd timer (eduscrap-notify.timer).
"""

import os
import sys
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("notify_users")

# Configurações de Conexão
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = os.getenv("MONGODB_DB", "hub_estudantes")

# Configurações de Notificação
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "notificacoes@eduscrap.uern.br")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GLOBAL_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def conectar_banco(uri: str = None, db_name: str = None):
    """Conecta ao MongoDB com timeout curto para evitar bloqueios."""
    from pymongo import MongoClient
    uri = uri or MONGODB_URI
    db_name = db_name or MONGODB_DB
    client = MongoClient(uri, serverSelectionTimeoutMS=4000)
    return client[db_name]


def buscar_editais_criticos(db, dias_max: int = 3) -> List[Dict[str, Any]]:
    """
    Localiza editais e oportunidades cujo prazo de inscrição expira em até `dias_max` dias.
    Varre as coleções padronizadas com batch_size para economizar memória.
    """
    hoje = datetime.now()
    limite = hoje + timedelta(days=dias_max, hours=23, minutes=59)

    colecoes = [
        "editais", "vagas_estagio", "vagas_bolsa", "vagas_ufersa",
        "vagas", "vagas_portal_uern", "oportunidades"
    ]
    nomes_existentes = set(db.list_collection_names())

    editais_criticos = []
    ids_vistos = set()

    filtro = {
        "data_vencimento": {
            "$gte": hoje - timedelta(hours=12),  # vigentes ou encerrando hoje
            "$lte": limite
        }
    }

    for col_nome in colecoes:
        if col_nome not in nomes_existentes:
            continue
        try:
            col = db[col_nome]
            cursor = col.find(filtro).batch_size(50)
            for doc in cursor:
                doc_id = str(doc.get("_id"))
                if doc_id in ids_vistos:
                    continue
                ids_vistos.add(doc_id)

                venc = doc.get("data_vencimento")
                dias_restantes = (venc.date() - hoje.date()).days if isinstance(venc, datetime) else 0

                doc["_id_str"] = doc_id
                doc["dias_restantes"] = dias_restantes
                doc["colecao_origem"] = col_nome
                editais_criticos.append(doc)
        except Exception as e:
            logger.warning(f"Erro ao consultar editais na coleção {col_nome}: {e}")

    logger.info(f"Total de {len(editais_criticos)} certames encontrados com encerramento em até {dias_max} dias.")
    return editais_criticos


def buscar_usuarios_interessados(db, id_edital: str) -> List[Dict[str, Any]]:
    """
    Localiza usuários cadastrados que favoritaram o edital especificado.
    Usa cursor com batch_size para manter consumo de memória ~100 MB.
    """
    try:
        from bson import ObjectId
        query = {
            "$or": [
                {"favoritos": id_edital},
                {"favoritos": ObjectId(id_edital)} if ObjectId.is_valid(id_edital) else {"favoritos": id_edital}
            ]
        }
    except Exception:
        query = {"favoritos": id_edital}

    usuarios = []
    try:
        cursor = db["usuarios"].find(query).batch_size(50)
        for u in cursor:
            usuarios.append(u)
    except Exception as e:
        logger.warning(f"Erro ao buscar favoritos para edital {id_edital}: {e}")

    return usuarios


def enviar_email_alerta(destinatario: str, edital: Dict[str, Any], dias_restantes: int) -> bool:
    """Envia alerta sobre o prazo limite do edital via SMTP."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and destinatario):
        logger.debug(f"[SMTP Simulado/Sem Credenciais] Notificação para {destinatario} sobre edital: {edital.get('titulo') or edital.get('nome')}")
        return False

    titulo = edital.get("titulo") or edital.get("nome") or "Edital Acadêmico"
    link = edital.get("link") or edital.get("url") or "#"
    venc_str = edital.get("data_vencimento").strftime("%d/%m/%Y") if isinstance(edital.get("data_vencimento"), datetime) else "Em breve"

    assunto = f"🚨 Atenção: Falta{'m' if dias_restantes > 1 else ''} {dias_restantes} dia(s) para o edital: {titulo[:45]}"

    corpo_texto = f"""Olá, estudante!

O edital que você favoritou no EduScrap está com inscrições se encerrando!

Edital: {titulo}
Origem: {edital.get('fonte', 'Universidade')}
Data Limite: {venc_str} ({dias_restantes} dias restantes)
Link do edital: {link}

Acesse o EduScrap para não perder nenhum prazo.
Equipe EduScrap
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = SMTP_FROM
    msg["To"] = destinatario
    msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, [destinatario], msg.as_string())
        logger.info(f"E-mail de alerta enviado para {destinatario} ({titulo[:30]})")
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail para {destinatario}: {e}")
        return False


def enviar_telegram_alerta(chat_id: str, edital: Dict[str, Any], dias_restantes: int, token: str = None) -> bool:
    """Dispara webhook Telegram via Bot API para notificação instantânea."""
    bot_token = token or TELEGRAM_BOT_TOKEN
    target_chat = chat_id or TELEGRAM_GLOBAL_CHAT_ID

    if not (bot_token and target_chat):
        logger.debug(f"[Telegram Simulado/Sem Token] Alerta telegram para chat_id {target_chat}")
        return False

    titulo = edital.get("titulo") or edital.get("nome") or "Edital Acadêmico"
    link = edital.get("link") or edital.get("url") or "#"
    venc_str = edital.get("data_vencimento").strftime("%d/%m/%Y") if isinstance(edital.get("data_vencimento"), datetime) else "Em breve"

    emoji_urgencia = "🔥" if dias_restantes <= 1 else "⚠️"
    mensagem = (
        f"{emoji_urgencia} *ALERTA DE PRAZO - EDUSCRAP*\n\n"
        f"O edital que você salvou encerra em breve:\n"
        f"📌 *{titulo}*\n"
        f"🏛️ *Origem:* {edital.get('fonte', 'Universidade')}\n"
        f"📅 *Prazo Limite:* {venc_str} ({dias_restantes} dia(s) restante(s))\n\n"
        f"🔗 [Acessar Edital Oficial]({link})"
    )

    url_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": mensagem,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        resp = requests.post(url_api, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"Notificação Telegram enviada com sucesso para chat {target_chat}")
            return True
        else:
            logger.warning(f"Telegram API retornou código {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Erro ao disparar alerta Telegram: {e}")
        return False


def processar_notificacoes(db = None) -> Dict[str, Any]:
    """
    Executa a rotina central de verificação e envio de notificações para editais críticos.
    Retorna sumário estatístico do processamento.
    """
    if db is None:
        db = conectar_banco()

    editais = buscar_editais_criticos(db, dias_max=3)

    total_emails = 0
    total_telegrams = 0
    total_usuarios_alertados = set()

    for edital in editais:
        id_str = edital["_id_str"]
        dias = edital["dias_restantes"]
        usuarios = buscar_usuarios_interessados(db, id_str)

        for user in usuarios:
            user_id = str(user.get("_id"))
            email = user.get("email")
            telegram_chat = user.get("telegram_chat_id") or TELEGRAM_GLOBAL_CHAT_ID

            if email:
                if enviar_email_alerta(email, edital, dias):
                    total_emails += 1
                    total_usuarios_alertados.add(user_id)

            if telegram_chat:
                if enviar_telegram_alerta(telegram_chat, edital, dias):
                    total_telegrams += 1
                    total_usuarios_alertados.add(user_id)

    resumo = {
        "sucesso": True,
        "editais_criticos": len(editais),
        "emails_enviados": total_emails,
        "telegrams_enviados": total_telegrams,
        "usuarios_notificados": len(total_usuarios_alertados),
        "executado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    logger.info(
        f"Processamento de notificações finalizado: "
        f"{len(editais)} editais críticos | "
        f"{total_emails} e-mails | "
        f"{total_telegrams} telegrams | "
        f"{len(total_usuarios_alertados)} usuários impactados."
    )
    return resumo


def main():
    logger.info("=== INICIANDO SERVIÇO DE NOTIFICAÇÃO EDUSCRAP (notify_users.py) ===")
    try:
        db = conectar_banco()
        resultado = processar_notificacoes(db)
        print(f"Sucesso: {resultado['editais_criticos']} editais críticos avaliados.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal no executor de notificações: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
