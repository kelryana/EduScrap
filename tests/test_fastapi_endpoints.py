import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_fastapi_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "mensagem" in data
    assert data.get("versao") == "1.3"

def test_fastapi_oportunidades_endpoint(client):
    """Testa o endpoint consolidado GET /api/oportunidades (UC01, Figura 4)"""
    with patch("backend.main.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find.return_value.limit.return_value = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "titulo": "Edital de Bolsas PROEX",
                "link": "https://uern.br/edital/123",
                "fonte": "PROEX/UERN",
                "categoria": "bolsa"
            }
        ]
        mock_db.list_collection_names.return_value = ["vagas_bolsa"]
        mock_db.__getitem__.return_value = mock_col

        response = client.get("/api/oportunidades?categoria=bolsa")
        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is True
        assert "dados" in data
        assert len(data["dados"]) == 1
        assert data["dados"][0]["titulo"] == "Edital de Bolsas PROEX"

def test_fastapi_admin_regras(client):
    """Testa endpoint administrativo de consulta de regras (UC12 / RF12)"""
    response = client.get("/api/admin/regras")
    assert response.status_code == 200
    data = response.json()
    assert data["sucesso"] is True
    assert "regras" in data
    assert "dates" in data["regras"]

def test_fastapi_admin_fontes(client):
    """Testa endpoint administrativo de listagem de fontes (UC10 / UC12)"""
    response = client.get("/api/admin/fontes")
    assert response.status_code == 200
    data = response.json()
    assert data["sucesso"] is True
    assert "fontes" in data
    assert "prae" in data["fontes"]
    assert "proex" in data["fontes"]

def test_fastapi_admin_logs(client):
    """Testa endpoint administrativo de consulta de logs isolados (UC11 / RF11)"""
    response = client.get("/api/admin/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["sucesso"] is True
    assert "logs" in data


def test_fastapi_auth_verificar_email(client):
    """Testa verificação de email existente e novo"""
    with patch("backend.main.db") as mock_db:
        mock_col = MagicMock()
        # Primeiro caso: não existe
        mock_col.find_one.return_value = None
        mock_db.__getitem__.return_value = mock_col

        resp = client.get("/api/auth/verificar-email?email=novo@aluno.uern.br")
        assert resp.status_code == 200
        assert resp.json()["existe"] is False
        assert resp.json()["valido"] is True

        # Segundo caso: já existe
        mock_col.find_one.return_value = {"email": "existe@aluno.uern.br"}
        resp2 = client.get("/api/auth/verificar-email?email=existe@aluno.uern.br")
        assert resp2.status_code == 200
        assert resp2.json()["existe"] is True


def test_fastapi_auth_redefinir_senha(client):
    """Testa endpoint de redefinição de senha"""
    with patch("backend.main.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one.return_value = {
            "_id": "607f1f77bcf86cd799439011",
            "email": "aluno@uern.br",
            "senha_hash": "antigo_hash"
        }
        mock_db.__getitem__.return_value = mock_col

        resp = client.post("/api/auth/redefinir-senha", json={
            "email": "aluno@uern.br",
            "nova_senha": "nova_senha_forte123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "sucesso" in data["message"].lower()
        mock_col.update_one.assert_called_once()

def test_fastapi_ciee_endpoint_titulo_rico(client):
    """Testa se o endpoint /api/ciee resolve títulos informativos e detalhados"""
    with patch("backend.main.db") as mock_db:
        mock_col = MagicMock()
        mock_col.count_documents.return_value = 1
        mock_col.find.return_value.skip.return_value.limit.return_value = [
            {
                "_id": "6148015abc12345678901234",
                "titulo": "Vaga CIEE",
                "nome_completo": "[6148015] Estágio - Seguridade Social (R$ 1.500,00)",
                "codigo": "6148015",
                "categoria": "Estágio",
                "area": "Seguridade Social",
                "salario": "R$ 1.500,00",
                "link": "https://portal.ciee.org.br/"
            }
        ]
        mock_db.__getitem__.return_value = mock_col

        resp = client.get("/api/ciee")
        assert resp.status_code == 200
        dados = resp.json()["dados"]
        assert len(dados) == 1
        assert dados[0]["titulo"] == "[6148015] Estágio - Seguridade Social (R$ 1.500,00)"
        assert dados[0]["nome"] == "[6148015] Estágio - Seguridade Social (R$ 1.500,00)"
        assert dados[0]["link"] == "https://portal.ciee.org.br/quero-uma-vaga/?codigoVaga=6148015"


