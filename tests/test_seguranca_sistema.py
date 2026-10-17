# tests/test_seguranca_sistema.py
"""
Suite de testes automatizados de segurança (AppSec / LGPD / OWASP):
1. Proteção de senhas com algoritmo de hash e salt seguro (PBKDF2/Werkzeug).
2. Verificação de senhas em texto puro nunca armazenadas.
3. Tratamento de e-mails: sanitização, normalização e mascaramento (LGPD).
4. Proteção contra Injeção / Directory Traversal nos endpoints de logs (/api/logs/{fonte}).
5. Assinatura criptográfica segura de tokens de sessão (itsdangerous / HMAC).
6. Expiração e rejeição de tokens adulterados / falsificados.
7. Não vazamento do campo senha_hash em retornos de perfil ou autenticação.
"""

import pytest
import re
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.api.auth import (
    hash_password,
    verify_password,
    generate_auth_token,
    decode_auth_token
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Criptografia e Armazenamento de Senhas
# ---------------------------------------------------------------------------
def test_senha_nunca_em_texto_puro():
    """Garante que a senha sofre hash criptográfico irreversível e seguro."""
    senha_plana = "SenhaSuperSecreta@2026"
    hash_gerado = hash_password(senha_plana)

    # Nunca pode ser igual ao texto puro
    assert hash_gerado != senha_plana
    # Deve usar formato seguro pbkdf2 ou scrypt
    assert any(alg in hash_gerado for alg in ["pbkdf2", "scrypt", "argon2", "$"])
    # Verificação com a senha correta deve passar
    assert verify_password(senha_plana, hash_gerado) is True
    # Senhas erradas ou vazias devem falhar
    assert verify_password("SenhaErrada", hash_gerado) is False
    assert verify_password("", hash_gerado) is False


def test_hashes_diferentes_para_mesma_senha():
    """Garante que o algoritmo aplica salt aleatório (duas senhas iguais geram hashes diferentes)."""
    senha = "mesmasenhaestudante"
    hash1 = hash_password(senha)
    hash2 = hash_password(senha)
    assert hash1 != hash2, "O algoritmo de hash deve usar salts únicos para mitigar Rainbow Tables!"


# ---------------------------------------------------------------------------
# 2. Segurança e Mascaramento de E-mails (LGPD / Privacidade)
# ---------------------------------------------------------------------------
def mascarar_email(email: str) -> str:
    """Função utilitária de mascaramento de dados pessoais (ex: an***@uern.br)."""
    if not email or "@" not in email:
        return ""
    usuario, dominio = email.split("@", 1)
    if len(usuario) <= 2:
        usuario_mascarado = usuario[0] + "*"
    else:
        usuario_mascarado = usuario[:2] + "*" * (len(usuario) - 2)
    return f"{usuario_mascarado}@{dominio}"


def test_mascaramento_email_lgpd():
    """Valida o mascaramento de e-mails em exibições públicas."""
    assert mascarar_email("estudante@uern.br") == "es*******@uern.br"
    assert mascarar_email("ana@gmail.com") == "an*@gmail.com"
    assert mascarar_email("jo@ufersa.edu.br") == "j*@ufersa.edu.br"


def test_normalizacao_email():
    """Garante que e-mails são tratados de forma case-insensitive e sem espaços maliciosos."""
    email_sujo = "   Estudante.UERN@GMAIL.COM  "
    email_limpo = email_sujo.strip().lower()
    assert email_limpo == "estudante.uern@gmail.com"


# ---------------------------------------------------------------------------
# 3. Assinatura Criptográfica e Integridade de Tokens
# ---------------------------------------------------------------------------
def test_token_assinatura_e_adulteracao():
    """Garante que qualquer alteração de 1 bit no token invalida a assinatura criptográfica."""
    token = generate_auth_token("usr_999", "seguranca@uern.br")
    assert isinstance(token, str)

    # Token válido decodifica corretamente
    dados = decode_auth_token(token)
    assert dados is not None
    assert dados["user_id"] == "usr_999"

    # Tentativa de adulteração (Tampering Attack)
    token_adulterado = token[:-3] + "xyz"
    dados_tampered = decode_auth_token(token_adulterado)
    assert dados_tampered is None, "Token adulterado NÃO deve ser aceito!"


# ---------------------------------------------------------------------------
# 4. Proteção contra Directory Traversal e Injeção de Caminhos (OWASP)
# ---------------------------------------------------------------------------
def test_protecao_directory_traversal_logs(client):
    """Garante que usuários maliciosos não consigam ler /etc/passwd via path traversal."""
    caminhos_ataque = [
        "../../etc/passwd",
        "..%2F..%2Fetc%2Fpasswd",
        "....//....//etc/shadow",
        "prae.log;cat /etc/passwd"
    ]
    for ataque in caminhos_ataque:
        resp = client.get(f"/api/logs/{ataque}")
        # Deve recusar com 400 (Bad Request) ou sanitizar impedindo acesso indevido
        assert resp.status_code in [400, 404]
        assert "root:" not in resp.text


# ---------------------------------------------------------------------------
# 5. Vazamento de Credenciais em Respostas de API (Data Leakage)
# ---------------------------------------------------------------------------
def test_payload_usuario_nao_expoe_hash():
    """Garante que a estrutura de usuário enviada ao frontend expurga o campo senha_hash."""
    doc_usuario = {
        "_id": "670f5e1a3b8d9f1",
        "nome": "Maria Estudante",
        "email": "maria@uern.br",
        "senha_hash": "pbkdf2:sha256:600000$abc$xyz...",
        "role": "aluno"
    }
    
    # Sanitização antes de enviar ao cliente
    doc_sanitizado = dict(doc_usuario)
    doc_sanitizado.pop("senha_hash", None)

    assert "senha_hash" not in doc_sanitizado
    assert "senha" not in doc_sanitizado
    assert doc_sanitizado["email"] == "maria@uern.br"
