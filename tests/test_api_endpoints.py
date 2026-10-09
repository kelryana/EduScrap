import pytest
from flask import Flask
from flask.testing import FlaskClient
from unittest.mock import patch, MagicMock
import mongomock
from pymongo import MongoClient

from backend.api.app import create_app

@pytest.fixture
def client():
  
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client

def test_estagios_endpoint(client):
  
    response = client.get("/api/vagas")
    assert response.status_code == 200
   
    data = response.get_json()
    assert "success" in data
    assert "count" in data
    assert "data" in data

def test_bolsas_endpoint(client):
  
    response = client.get("/api/editais")
    assert response.status_code == 200

    data = response.get_json()
    assert "success" in data
    assert "count" in data
    assert "data" in data

def test_pesquisar_endpoint(client):
    """Test /api/oportunidades endpoint with various parameters (closest to pesquisar)"""
    # Test basic search
    response = client.get("/api/oportunidades")
    assert response.status_code == 200
    
    # Test search with filters
    response = client.get("/api/oportunidades?tipo=estagio")
    assert response.status_code == 200
    
    # Test search with multiple parameters
    response = client.get("/api/oportunidades?area=tecnologia&status=aberto")
    assert response.status_code == 200

def test_buscar_tudo_endpoint(client):
    """Test /api/oportunidades endpoint (closest equivalent to buscar-tudo)"""
    response = client.get("/api/oportunidades")
    assert response.status_code == 200

def test_noticias_endpoint(client):
    """Test /api/noticias endpoint"""
    response = client.get("/api/noticias")
    assert response.status_code == 200
    
    # Check that response contains expected fields
    data = response.get_json()
    assert "success" in data
    assert "count" in data
    assert "data" in data

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.get_json()
    assert "message" in data
    assert "endpoints" in data

def test_vagas_endpoint_with_filters(client):
    """Test /api/vagas endpoint with filters"""
    response = client.get("/api/vagas?area=tecnologia")
    assert response.status_code == 200
    
    response = client.get("/api/vagas?fonte=uern")
    assert response.status_code == 200

def test_editais_endpoint_with_filters(client):
    """Test /api/editais endpoint with filters"""
    response = client.get("/api/editais?status=aberto")
    assert response.status_code == 200
    
    response = client.get("/api/editais?fonte=ciee")
    assert response.status_code == 200

def test_get_oportunidade_by_id(client):
    """Test getting specific opportunity by ID"""
    # This will likely return 404 since we're using mock DB, but should not error
    response = client.get("/api/oportunidades/1")
    # Could be 404 if not found, or 200 if found - both are valid responses
    assert response.status_code in [200, 404]

def test_api_response_structure(client):
    """Test that API responses follow consistent structure"""
    endpoints = ["/api/vagas", "/api/editais", "/api/noticias", "/api/oportunidades"]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        
        data = response.get_json()
        # Verify standard response structure
        assert isinstance(data, dict)
        assert "success" in data
        assert "count" in data  # or "data" in data