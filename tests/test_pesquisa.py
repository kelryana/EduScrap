# -*- coding: utf-8 -*-
"""
Testes específicos para a busca textual unificada (/api/pesquisar).
Valida:
1. Retorno de resultados relevantes para termos existentes (com documentos simulados ou reais).
2. Retorno vazio limpo (200 com lista vazia) para termos sem correspondência.
3. Validação de tamanho mínimo do termo (HTTP 422 para termo < 2 caracteres).
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_pesquisa_termo_existente_mock():
    """Busca por termo que existe retorna lista com itens enriquecidos."""
    with patch("backend.main.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find.return_value.limit.return_value = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "titulo": "Edital Bolsa PROEX UERN 2026",
                "link": "https://uern.br/edital/bolsa_123.pdf",
                "fonte": "PROEX/UERN",
                "categoria": "Bolsa"
            }
        ]
        mock_db.list_collection_names.return_value = ["vagas_bolsa"]
        mock_db.__getitem__.return_value = mock_col

        resp = client.get("/api/pesquisar?termo=bolsa")
        assert resp.status_code == 200
        dados = resp.json()
        assert isinstance(dados, list)
        assert len(dados) == 1
        assert "Bolsa" in dados[0]["titulo"]


def test_pesquisa_termo_inexistente():
    """Busca por termo que não existe deve retornar HTTP 200 com lista vazia (não erro 500)."""
    resp = client.get("/api/pesquisar?termo=termo_inexistente_xyz_123456")
    assert resp.status_code == 200
    dados = resp.json()
    assert isinstance(dados, list)
    assert len(dados) == 0


def test_pesquisa_termo_muito_curto():
    """Validação de entrada: termo com menos de 2 caracteres deve retornar 422."""
    resp = client.get("/api/pesquisar?termo=a")
    assert resp.status_code == 422
