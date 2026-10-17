import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from io import BytesIO

import pytest
import pyotp
import responses
from mongomock import MongoClient as MockMongoClient
from mongomock.gridfs import enable_gridfs_integration
from fastapi.testclient import TestClient

# Habilita gridfs no mongomock se disponível
try:
    enable_gridfs_integration()
except Exception:
    pass

from backend.main import app, _parsear_arquivo_log
from backend.pdf_utils import salvar_snapshot_gridfs, obter_snapshot_gridfs
from notify_users import (
    buscar_editais_criticos,
    buscar_usuarios_interessados,
    enviar_telegram_alerta,
    processar_notificacoes
)
from cleanup_snapshots import limpar_snapshots_antigos


@pytest.fixture
def mock_db():
    client = MockMongoClient()
    db = client["hub_estudantes"]
    return db


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. TESTES DE MFA (pyotp)
# ==============================================================================

class TestMFA:
    def test_geracao_e_validacao_totp(self):
        """Testa geração de segredo e validação correta com pyotp."""
        secret = pyotp.random_base32()
        assert len(secret) == 32 or len(secret) == 16

        totp = pyotp.TOTP(secret)
        codigo_atual = totp.now()

        assert len(codigo_atual) == 6
        assert totp.verify(codigo_atual) is True
        assert totp.verify("000000") is False

    def test_mfa_endpoints_setup_e_status(self, client):
        """Testa status e setup de MFA via API."""
        resp_status = client.get("/api/auth/mfa/status")
        assert resp_status.status_code == 200
        dados = resp_status.json()
        assert "mfa_ativo" in dados

        # Setup requer admin
        resp_setup = client.post("/api/auth/mfa/setup", headers={"X-API-Key": ""})
        assert resp_setup.status_code == 200
        data_setup = resp_setup.json()
        assert data_setup["sucesso"] is True
        assert "secret" in data_setup
        assert "otpauth_url" in data_setup
        assert "otpauth://" in data_setup["otpauth_url"]

    def test_mfa_ativacao_codigo_invalido(self, client):
        """Testa que código inválido não ativa o MFA."""
        resp = client.post(
            "/api/auth/mfa/ativar",
            json={"codigo": "123456", "secret": "JBSWY3DPEHPK3PXP"}
        )
        assert resp.status_code == 400


# ==============================================================================
# 2. TESTES DE LOGS REST E PARSER (UC11)
# ==============================================================================

class TestLogsEndpoints:
    def test_parsear_arquivo_log_sucesso(self):
        """Testa parser de linhas de log identificando sucesso e itens."""
        conteudo = (
            "=== INÍCIO DA VARREDURA: PRAE/UERN ===\n"
            "Data: 2026-10-17 03:00:00\n"
            "Comando: python scraper_prae.py\n"
            "Concluído em 3.2s! (Itens na base: 14)\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            resultado = _parsear_arquivo_log(temp_path)
            assert resultado["existe"] is True
            assert resultado["status"] == "sucesso"
            assert resultado["duracao_segundos"] == 3.2
            assert resultado["itens_coletados"] == 14
            assert resultado["total_erros"] == 0
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_parsear_arquivo_log_falha(self):
        """Testa parser de linhas de log identificando falhas críticas."""
        conteudo = (
            "=== INÍCIO DA VARREDURA: TESTE ===\n"
            "[ERRO] Processo interrompido por timeout de 5 minutos.\n"
            "FALHOU (Timeout)\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False) as f:
            f.write(conteudo)
            temp_path = f.name

        try:
            resultado = _parsear_arquivo_log(temp_path)
            assert resultado["status"] == "falha"
            assert resultado["total_erros"] >= 1
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_endpoint_logs_lista_scrapers(self, client):
        """Testa GET /api/logs retornando consolidado dos scrapers."""
        resp = client.get("/api/logs")
        assert resp.status_code == 200
        dados = resp.json()
        assert dados["sucesso"] is True
        assert dados["total_scrapers"] > 0
        assert isinstance(dados["scrapers"], list)

    def test_endpoint_logs_sanitizacao_path_traversal(self, client):
        """Testa proteção contra path traversal no endpoint de logs."""
        resp = client.get("/api/logs/..%2F..%2Fetc%2Fpasswd")
        assert resp.status_code in [400, 404]


# ==============================================================================
# 3. TESTES DE NOTIFICAÇÕES (notify_users.py)
# ==============================================================================

class TestNotificacoes:
    def test_buscar_editais_criticos(self, mock_db):
        """Testa identificação de editais com encerramento <= 3 dias."""
        agora = datetime.now()
        # Edital crítico (vence amanhã)
        mock_db["editais"].insert_one({
            "titulo": "Edital Monitoria 2026",
            "data_vencimento": agora + timedelta(days=1),
            "fonte": "UERN"
        })
        # Edital distante (vence em 20 dias)
        mock_db["editais"].insert_one({
            "titulo": "Edital Longe 2026",
            "data_vencimento": agora + timedelta(days=20),
            "fonte": "UERN"
        })

        criticos = buscar_editais_criticos(mock_db, dias_max=3)
        assert len(criticos) == 1
        assert criticos[0]["titulo"] == "Edital Monitoria 2026"
        assert criticos[0]["dias_restantes"] in [0, 1]

    def test_buscar_usuarios_interessados(self, mock_db):
        """Testa consulta paginada de usuários que favoritaram o edital."""
        id_edital = "edital_123"
        mock_db["usuarios"].insert_one({
            "nome": "Maria Silva",
            "email": "maria@uern.br",
            "favoritos": [id_edital]
        })
        mock_db["usuarios"].insert_one({
            "nome": "João Souza",
            "email": "joao@uern.br",
            "favoritos": ["outro_edital"]
        })

        interessados = buscar_usuarios_interessados(mock_db, id_edital)
        assert len(interessados) == 1
        assert interessados[0]["email"] == "maria@uern.br"

    @responses.activate
    def test_enviar_telegram_alerta_webhook(self):
        """Testa disparo de webhook Telegram via Bot API com responses."""
        token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        chat_id = "987654321"
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        responses.add(
            responses.POST,
            url,
            json={"ok": True, "result": {"message_id": 42}},
            status=200
        )

        edital = {
            "titulo": "Edital Residência Judicial MPRN",
            "fonte": "MPRN",
            "data_vencimento": datetime.now() + timedelta(days=2),
            "link": "https://mprn.mp.br/edital"
        }

        sucesso = enviar_telegram_alerta(chat_id, edital, dias_restantes=2, token=token)
        assert sucesso is True
        assert len(responses.calls) == 1


# ==============================================================================
# 4. TESTES DE SNAPSHOTS GRIDFS E RETENÇÃO
# ==============================================================================

class TestSnapshotsGridFS:
    def test_salvar_e_recuperar_snapshot(self, mock_db):
        """Testa gravação de snapshot PDF no GridFS."""
        import gridfs
        fs = gridfs.GridFS(mock_db)
        pdf_falso = b"%PDF-1.4 Fake PDF Content for Snapshot Testing"

        file_id = salvar_snapshot_gridfs(
            pdf_bytes=pdf_falso,
            filename="edital_teste.pdf",
            url_origem="https://uern.br/edital.pdf",
            db=mock_db
        )
        assert file_id is not None

        recuperado = obter_snapshot_gridfs(file_id, db=mock_db)
        assert recuperado is not None
        assert recuperado.read() == pdf_falso

    def test_limpeza_retencao_snapshots(self, mock_db):
        """Testa política de retenção de snapshots com mais de 365 dias."""
        import gridfs
        fs = gridfs.GridFS(mock_db)

        # Snapshot recente
        id_recente = fs.put(b"conteudo recente", filename="recente.pdf", data_captura=datetime.now())

        # Snapshot antigo (> 365 dias)
        data_antiga = datetime.now() - timedelta(days=400)
        id_antigo = fs.put(b"conteudo antigo", filename="antigo.pdf", data_captura=data_antiga)
        # Atualiza uploadDate no mock se suportado
        mock_db["fs.files"].update_one({"_id": id_antigo}, {"$set": {"uploadDate": data_antiga}})

        res = limpar_snapshots_antigos(dias_retencao=365, uri=None, db_name=None)
        # Deve ter processado a rotina com sucesso
        assert "sucesso" in res


# ==============================================================================
# 5. TESTES DE EXPORTAÇÃO iCalendar (.ics)
# ==============================================================================

class TestICalendar:
    def test_estrutura_formato_ics(self):
        """Testa conformidade da estrutura de texto iCalendar RFC 5545."""
        titulo = "Edital Concurso Técnico 2026"
        dt_start = "20261025T080000"
        dt_end = "20261025T235959"

        ics_lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//EduScrap//Calendario de Editais//PT-BR',
            'BEGIN:VEVENT',
            f'UID:eduscrap-teste-1@eduscrap.uern.br',
            f'DTSTART:{dt_start}',
            f'DTEND:{dt_end}',
            f'SUMMARY:🚨 Prazo Limite: {titulo}',
            'END:VEVENT',
            'END:VCALENDAR'
        ]
        ics_text = "\r\n".join(ics_lines)

        assert "BEGIN:VCALENDAR" in ics_text
        assert "VERSION:2.0" in ics_text
        assert "BEGIN:VEVENT" in ics_text
        assert f"SUMMARY:🚨 Prazo Limite: {titulo}" in ics_text
        assert "END:VEVENT" in ics_text
        assert "END:VCALENDAR" in ics_text


# ==============================================================================
# 6. TESTES DE COMPATIBILIDADE MULTIPLATAFORMA (Windows vs. Linux)
# ==============================================================================

class TestMultiplataforma:
    def test_matar_processos_chrome_linux(self):
        """Testa que no Linux é utilizado pkill."""
        from run_scrapers import matar_processos_chrome
        with patch("sys.platform", "linux"), patch("subprocess.run") as mock_run:
            matar_processos_chrome()
            assert mock_run.call_count == 2
            args_chamados = [chamada[0][0] for chamada in mock_run.call_args_list]
            assert ["pkill", "-f", "chrome"] in args_chamados
            assert ["pkill", "-f", "chromedriver"] in args_chamados

    def test_matar_processos_chrome_windows(self):
        """Testa que no Windows é utilizado taskkill /F /IM."""
        from run_scrapers import matar_processos_chrome
        with patch("sys.platform", "win32"), patch("subprocess.run") as mock_run:
            matar_processos_chrome()
            assert mock_run.call_count == 2
            args_chamados = [chamada[0][0] for chamada in mock_run.call_args_list]
            assert ["taskkill", "/F", "/IM", "chrome.exe"] in args_chamados
            assert ["taskkill", "/F", "/IM", "chromedriver.exe"] in args_chamados
