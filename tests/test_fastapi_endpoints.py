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
