# backend/api/routes.py
from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
import re
from src.normalizer.database import MongoDBHandler
from .auth import (
    hash_password,
    verify_password,
    generate_auth_token,
    token_required,
    token_optional
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria blueprint para rotas da API
api_routes = Blueprint('api', __name__, url_prefix='/api')

# Inicializa handler do MongoDB
db_handler = None

def get_db_handler():
   
    global db_handler
    if db_handler is None:
        try:
            db_handler = MongoDBHandler()
        except Exception as e:
            logger.error(f"Erro ao inicializar MongoDB: {str(e)}")
            return None
    return db_handler

@api_routes.route('/oportunidades', methods=['GET'])
@token_optional
def get_oportunidades():
    """Endpoint para listar oportunidades (editais + vagas) com filtros"""
    db = get_db_handler()

    if db is None:
        return jsonify({
            'success': False,
            'error': 'MongoDB não disponível',
            'data': []
        }), 503

    args = request.args
    area = args.get('area')
    status = args.get('status')
    tipo = args.get('tipo')

    try:
        oportunidades = db.get_oportunidades(area=area, status=status, tipo=tipo)

        # Se o usuário estiver autenticado, sinaliza os itens que ele já favoritou
        if getattr(request, 'current_user', None):
            fav_ids = set(request.current_user.get('favoritos', []))
            for op in oportunidades:
                op['favorito'] = str(op.get('_id')) in fav_ids

        logger.info(f"Retornando {len(oportunidades)} oportunidades")
        return jsonify({
            'success': True,
            'count': len(oportunidades),
            'data': oportunidades
        })
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_routes.route('/editais', methods=['GET'])
@token_optional
def get_editais():
   
    db = get_db_handler()

    if db is None:
        return jsonify({
            'success': False,
            'error': 'MongoDB não disponível',
            'data': []
        }), 503

    args = request.args
    status = args.get('status')
    fonte = args.get('fonte')

    try:
        editais = db.get_editais(status=status, fonte=fonte)

        if getattr(request, 'current_user', None):
            fav_ids = set(request.current_user.get('favoritos', []))
            for edital in editais:
                edital['favorito'] = str(edital.get('_id')) in fav_ids

        logger.info(f"Retornando {len(editais)} editais")
        return jsonify({
            'success': True,
            'count': len(editais),
            'data': editais
        })
    except Exception as e:
        logger.error(f"Erro ao buscar editais: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_routes.route('/vagas', methods=['GET'])
@token_optional
def get_vagas():
  
    db = get_db_handler()

    if db is None:
        return jsonify({
            'success': False,
            'error': 'MongoDB não disponível',
            'data': []
        }), 503

    args = request.args
    area = args.get('area')
    fonte = args.get('fonte')

    try:
        vagas = db.get_vagas(area=area, fonte=fonte)

        if getattr(request, 'current_user', None):
            fav_ids = set(request.current_user.get('favoritos', []))
            for vaga in vagas:
                vaga['favorito'] = str(vaga.get('_id')) in fav_ids

        logger.info(f"Retornando {len(vagas)} vagas")
        return jsonify({
            'success': True,
            'count': len(vagas),
            'data': vagas
        })
    except Exception as e:
        logger.error(f"Erro ao buscar vagas: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_routes.route('/noticias', methods=['GET'])
def get_noticias():
   
    db = get_db_handler()

    if db is None:
        return jsonify({
            'success': False,
            'error': 'MongoDB não disponível',
            'data': []
        }), 503

    args = request.args
    categoria = args.get('categoria')

    try:
        noticias = db.get_noticias(categoria=categoria)
        logger.info(f"Retornando {len(noticias)} notícias")
        return jsonify({
            'success': True,
            'count': len(noticias),
            'data': noticias
        })
    except Exception as e:
        logger.error(f"Erro ao buscar notícias: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_routes.route('/oportunidades/<string:id>', methods=['GET'])
@api_routes.route('/oportunidades/<int:id>', methods=['GET'])
@token_optional
def get_oportunidade_by_id(id):
   
    db = get_db_handler()

    if db is None:
        return jsonify({
            'success': False,
            'error': 'MongoDB não disponível'
        }), 503

    try:
        # Tenta buscar em todas as coleções
        for collection in ['editais', 'vagas', 'noticias']:
            item = db.get_by_id(str(id), collection=collection)
            if item:
                if getattr(request, 'current_user', None):
                    fav_ids = set(request.current_user.get('favoritos', []))
                    item['favorito'] = str(item.get('_id')) in fav_ids
                return jsonify({
                    'success': True,
                    'data': item
                })

        return jsonify({
            'success': False,
            'error': 'Oportunidade não encontrada'
        }), 404
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidade por ID: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_routes.route('/auth/register', methods=['POST'])
def register():
  
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    data = request.get_json(silent=True) or {}
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')
    matricula = data.get('matricula', '').strip()
    cursos = data.get('cursos', [])
    areas = data.get('areas', [])
    receber_emails = data.get('receber_emails', True)

    # Validações básicas
    if not nome:
        return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400

    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Email válido é obrigatório'}), 400

    if not senha or len(senha) < 6:
        return jsonify({'success': False, 'error': 'Senha deve ter no mínimo 6 caracteres'}), 400

    # Normaliza listas de preferências
    if isinstance(cursos, str):
        cursos = [c.strip() for c in cursos.split(',') if c.strip()]
    if isinstance(areas, str):
        areas = [a.strip() for a in areas.split(',') if a.strip()]

    # Cria usuário
    senha_hash = hash_password(senha)
    user_payload = {
        'nome': nome,
        'email': email,
        'senha_hash': senha_hash,
        'matricula': matricula,
        'preferencias': {
            'cursos': cursos,
            'areas': areas,
            'receber_emails': bool(receber_emails)
        },
        'favoritos': []
    }

    user_id = db.create_user(user_payload)
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Já existe uma conta cadastrada com este email.'
        }), 409

    token = generate_auth_token(user_id, email)
    user_data = db.find_user_by_id(user_id)

    return jsonify({
        'success': True,
        'message': 'Conta criada com sucesso!',
        'token': token,
        'user': user_data
    }), 201


@api_routes.route('/auth/login', methods=['POST'])
def login():
   
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    if not email or not senha:
        return jsonify({'success': False, 'error': 'Email e senha são obrigatórios'}), 400

    user = db.find_user_by_email(email)
    if not user:
        return jsonify({'success': False, 'error': 'Email ou senha incorretos'}), 401

    senha_hash = user.get('senha_hash', '')
    if not verify_password(senha, senha_hash):
        return jsonify({'success': False, 'error': 'Email ou senha incorretos'}), 401

    token = generate_auth_token(user['_id'], user['email'])

    # Não expõe o hash da senha no retorno
    user.pop('senha_hash', None)

    return jsonify({
        'success': True,
        'message': 'Login realizado com sucesso!',
        'token': token,
        'user': user
    })


@api_routes.route('/auth/me', methods=['GET'])
@token_required
def get_current_user_profile():
   
    return jsonify({
        'success': True,
        'user': request.current_user
    })


@api_routes.route('/auth/preferencias', methods=['PUT'])
@token_required
def update_preferences():
   
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    data = request.get_json(silent=True) or {}
    user_id = request.current_user['_id']

    preferencias = {}
    if 'cursos' in data:
        preferencias['cursos'] = data['cursos'] if isinstance(data['cursos'], list) else [data['cursos']]
    if 'areas' in data:
        preferencias['areas'] = data['areas'] if isinstance(data['areas'], list) else [data['areas']]
    if 'receber_emails' in data:
        preferencias['receber_emails'] = bool(data['receber_emails'])

    sucesso = db.update_user_preferences(user_id, preferencias)
    if not sucesso:
        return jsonify({'success': False, 'error': 'Falha ao atualizar preferências'}), 500

    updated_user = db.find_user_by_id(user_id)
    return jsonify({
        'success': True,
        'message': 'Preferências atualizadas com sucesso!',
        'user': updated_user
    })


@api_routes.route('/auth/perfil', methods=['PUT'])
@token_required
def update_profile():
    
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    data = request.get_json(silent=True) or {}
    user_id = request.current_user['_id']

    sucesso = db.update_user_profile(user_id, data)
    if not sucesso:
        return jsonify({'success': False, 'error': 'Falha ao atualizar perfil'}), 500

    updated_user = db.find_user_by_id(user_id)
    return jsonify({
        'success': True,
        'message': 'Perfil atualizado com sucesso!',
        'user': updated_user
    })

@api_routes.route('/favoritos', methods=['GET'])
@token_required
def list_favoritos():
  
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    user_id = request.current_user['_id']
    favoritos = db.get_user_favoritos(user_id)

    return jsonify({
        'success': True,
        'count': len(favoritos),
        'data': favoritos
    })


@api_routes.route('/favoritos/<string:id>', methods=['POST'])
@token_required
def add_favorito_route(id):
    
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    user_id = request.current_user['_id']
    sucesso = db.add_favorito(user_id, id)

    if not sucesso:
        return jsonify({'success': False, 'error': 'Não foi possível favoritar a oportunidade'}), 400

    return jsonify({
        'success': True,
        'message': 'Oportunidade adicionada aos favoritos com sucesso!',
        'oportunidade_id': id
    })


@api_routes.route('/favoritos/<string:id>', methods=['DELETE'])
@token_required
def remove_favorito_route(id):
   
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    user_id = request.current_user['_id']
    sucesso = db.remove_favorito(user_id, id)

    if not sucesso:
        return jsonify({'success': False, 'error': 'Não foi possível remover dos favoritos'}), 400

    return jsonify({
        'success': True,
        'message': 'Oportunidade removida dos favoritos com sucesso!',
        'oportunidade_id': id
    })

@api_routes.route('/feed/personalizado', methods=['GET'])
@token_required
def get_feed_personalizado_route():
    
    db = get_db_handler()
    if db is None:
        return jsonify({'success': False, 'error': 'MongoDB não disponível'}), 503

    user_id = request.current_user['_id']
    limit = int(request.args.get('limit', 50))

    oportunidades = db.get_feed_personalizado(user_id, limit=limit)

    return jsonify({
        'success': True,
        'count': len(oportunidades),
        'preferencias': request.current_user.get('preferencias', {}),
        'data': oportunidades
    })

@api_routes.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint não encontrado'
    }), 404


@api_routes.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor'
    }), 500
