# backend/api/auth.py

import os
from functools import wraps
from typing import Dict, Optional, Any
from flask import request, jsonify
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

# Configurações de autenticação
SECRET_KEY = os.getenv("SECRET_KEY", "eduscrap-jwt-secret-key-uern-2026")
AUTH_SALT = "eduscrap-auth-salt-v1"
TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE", 86400 * 7))  # 7 dias por padrão

serializer = URLSafeTimedSerializer(SECRET_KEY, salt=AUTH_SALT)


def hash_password(password: str) -> str:
   
    return generate_password_hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    
    if not password or not hashed_password:
        return False
    return check_password_hash(hashed_password, password)


def generate_auth_token(user_id: str, email: str) -> str:
   
    payload = {
        "user_id": str(user_id),
        "email": email.strip().lower()
    }
    return serializer.dumps(payload)


def decode_auth_token(token: str, max_age: int = TOKEN_MAX_AGE) -> Optional[Dict[str, Any]]:
  
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except SignatureExpired:
        logger.warning("Token expirado")
        return None
    except BadSignature:
        logger.warning("Token com assinatura inválida")
        return None
    except Exception as e:
        logger.error(f"Erro ao decodificar token: {str(e)}")
        return None


def get_token_from_request() -> Optional[str]:
   
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        elif len(parts) == 1:
            return parts[0]
            
    # Fallback para header alternativo ou query param
    token = request.headers.get("X-Access-Token")
    if token:
        return token
        
    return request.args.get("token")


def token_required(f):
    
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()

        if not token:
            return jsonify({
                "success": False,
                "error": "Token de autenticação não fornecido",
                "code": "TOKEN_MISSING"
            }), 401

        payload = decode_auth_token(token)
        if not payload:
            return jsonify({
                "success": False,
                "error": "Token inválido ou expirado",
                "code": "TOKEN_INVALID"
            }), 401

        from .routes import get_db_handler
        db = get_db_handler()
        if db is None:
            return jsonify({
                "success": False,
                "error": "Banco de dados não disponível"
            }), 503

        user = db.find_user_by_id(payload.get("user_id"))
        if not user:
            return jsonify({
                "success": False,
                "error": "Usuário associado ao token não encontrado",
                "code": "USER_NOT_FOUND"
            }), 401

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def token_optional(f):
   
    @wraps(f)
    def decorated(*args, **kwargs):
        request.current_user = None
        token = get_token_from_request()
        if token:
            payload = decode_auth_token(token)
            if payload:
                from .routes import get_db_handler
                db = get_db_handler()
                if db:
                    request.current_user = db.find_user_by_id(payload.get("user_id"))
        return f(*args, **kwargs)

    return decorated
