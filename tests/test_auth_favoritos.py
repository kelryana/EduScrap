# tests/test_auth_favoritos.py

import pytest
from unittest.mock import patch
import mongomock
from flask import json
from backend.api.app import create_app
from backend.api.auth import (
    hash_password,
    verify_password,
    generate_auth_token,
    decode_auth_token
)
from src.normalizer.database import MongoDBHandler


@pytest.fixture
def mock_mongo_client():
    return mongomock.MongoClient()


@pytest.fixture
def db_handler(mock_mongo_client):
    handler = MongoDBHandler(client=mock_mongo_client, db_name="eduscrap_test_auth")
    handler.create_indexes()
    return handler


@pytest.fixture
def app(db_handler):
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    
    # Injeta db_handler mockado em routes
    with patch('backend.api.routes.get_db_handler', return_value=db_handler):
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

def test_password_hashing():
    pwd = "minhasenha123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("outrasenha", hashed) is False
    assert verify_password("", hashed) is False


def test_auth_token_generation_and_decoding():
    token = generate_auth_token("user_123", "aluno@uern.br")
    assert isinstance(token, str)
    
    payload = decode_auth_token(token)
    assert payload is not None
    assert payload['user_id'] == "user_123"
    assert payload['email'] == "aluno@uern.br"


def test_auth_token_invalid():
    assert decode_auth_token("token_invalido_qualquer") is None

def test_database_user_crud(db_handler):
    user_payload = {
        'nome': 'Ana Silva',
        'email': 'ana@uern.br',
        'senha_hash': hash_password('senha123'),
        'matricula': '2024101',
        'preferencias': {
            'cursos': ['Ciência da Computação'],
            'areas': ['Tecnologia'],
            'receber_emails': True
        }
    }
    user_id = db_handler.create_user(user_payload)
    assert user_id is not None

    # Tentar criar com mesmo email deve falhar
    assert db_handler.create_user(user_payload) is None

    # Buscar por email
    found_by_email = db_handler.find_user_by_email('ana@uern.br')
    assert found_by_email is not None
    assert found_by_email['nome'] == 'Ana Silva'

    # Buscar por id (não deve retornar senha_hash por padrão)
    found_by_id = db_handler.find_user_by_id(user_id)
    assert found_by_id is not None
    assert 'senha_hash' not in found_by_id

    # Atualizar preferências
    sucesso = db_handler.update_user_preferences(user_id, {
        'cursos': ['Ciência da Computação', 'Sistemas de Informação'],
        'areas': ['Tecnologia', 'Inovação'],
        'receber_emails': False
    })
    assert sucesso is True
    updated = db_handler.find_user_by_id(user_id)
    assert 'Sistemas de Informação' in updated['preferencias']['cursos']
    assert updated['preferencias']['receber_emails'] is False


def test_database_favoritos(db_handler):
    # Cria edital teste
    edital_id = db_handler.insert_edital({
        'titulo': 'Edital Monitoria Computação 2026',
        'fonte': 'UERN',
        'link': 'http://uern.br/monitoria',
        'status': 'Aberto',
        'areas': ['Tecnologia', 'Computação']
    })

    # Cria usuário
    user_id = db_handler.create_user({
        'nome': 'Carlos',
        'email': 'carlos@uern.br',
        'senha_hash': hash_password('senha123')
    })

    # Adiciona aos favoritos
    assert db_handler.add_favorito(user_id, edital_id) is True
    
    # Lista favoritos
    favs = db_handler.get_user_favoritos(user_id)
    assert len(favs) == 1
    assert favs[0]['_id'] == edital_id
    assert favs[0]['favorito'] is True

    # Remove dos favoritos
    assert db_handler.remove_favorito(user_id, edital_id) is True
    favs_after = db_handler.get_user_favoritos(user_id)
    assert len(favs_after) == 0

def test_api_register_and_login_flow(client, db_handler):
    # 1. Registro
    reg_response = client.post('/api/auth/register', json={
        'nome': 'Mariana Souza',
        'email': 'mariana@uern.br',
        'senha': 'segredoForte123',
        'matricula': '2025102',
        'cursos': ['Direito', 'Administração'],
        'areas': ['Humanas']
    })
    assert reg_response.status_code == 201
    reg_data = reg_response.get_json()
    assert reg_data['success'] is True
    assert 'token' in reg_data
    token = reg_data['token']

    # 2. Login com sucesso
    login_response = client.post('/api/auth/login', json={
        'email': 'mariana@uern.br',
        'senha': 'segredoForte123'
    })
    assert login_response.status_code == 200
    login_data = login_response.get_json()
    assert login_data['success'] is True
    assert 'token' in login_data

    # 3. Login com senha errada
    fail_response = client.post('/api/auth/login', json={
        'email': 'mariana@uern.br',
        'senha': 'senhaIncorreta'
    })
    assert fail_response.status_code == 401

    # 4. Rota protegida /api/auth/me
    headers = {'Authorization': f'Bearer {token}'}
    me_response = client.get('/api/auth/me', headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.get_json()
    assert me_data['user']['nome'] == 'Mariana Souza'

    # 5. Rota protegida sem token
    no_token_response = client.get('/api/auth/me')
    assert no_token_response.status_code == 401


def test_api_favoritos_and_feed(client, db_handler):
    # Registra usuário
    reg_res = client.post('/api/auth/register', json={
        'nome': 'Lucas Lima',
        'email': 'lucas@uern.br',
        'senha': 'minhasenha123',
        'cursos': ['Ciência da Computação'],
        'areas': ['Tecnologia']
    })
    token = reg_res.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # Insere edital compatível
    edital_id = db_handler.insert_edital({
        'titulo': 'Edital de Estágio em TI UERN',
        'fonte': 'UERN',
        'link': 'http://uern.br/ti',
        'status': 'Aberto',
        'areas': ['Tecnologia']
    })

    # Favoritar
    fav_post = client.post(f'/api/favoritos/{edital_id}', headers=headers)
    assert fav_post.status_code == 200

    # Listar favoritos
    fav_list = client.get('/api/favoritos', headers=headers)
    assert fav_list.status_code == 200
    fav_data = fav_list.get_json()
    assert fav_data['count'] == 1
    assert fav_data['data'][0]['_id'] == edital_id

    # Consultar feed personalizado
    feed_res = client.get('/api/feed/personalizado', headers=headers)
    assert feed_res.status_code == 200
    feed_data = feed_res.get_json()
    assert feed_data['success'] is True
    assert len(feed_data['data']) >= 1

    # Desfavoritar
    del_fav = client.delete(f'/api/favoritos/{edital_id}', headers=headers)
    assert del_fav.status_code == 200

    fav_list_after = client.get('/api/favoritos', headers=headers)
    assert fav_list_after.get_json()['count'] == 0
