import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_feed_performance_under_1_second(client):
    """
    Testa o Requisito Não Funcional RNF01:
    'A consulta ao feed deve responder em menos de 1 segundo.'
    """
    # Mock das coleções para garantir execução limpa e sem dependência de banco externo
    with patch("backend.main.db") as mock_db:
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "titulo": "Edital de Estágio em TI",
                "link": "https://uern.br/edital/1",
                "data_vencimento": "2026-12-31",
                "fonte": "PRAE",
                "status": "vigente"
            }
        ]
        mock_collection.find.return_value = mock_cursor
        mock_collection.count_documents.return_value = 1
        mock_db.__getitem__.return_value = mock_collection

        start_time = time.time()
        response = client.get("/api/estagios?pagina=1&limite=6")
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration < 1.0, f"Tempo de resposta do feed ({duration:.3f}s) excedeu o limite de 1.0s (RNF01)"
