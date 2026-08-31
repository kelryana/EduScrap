#--- src/api/routes.py

API Routes - Rotas da API RESTful

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from src.normalizer.database import MongoDBHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria blueprint para rotas da API
api_routes = Blueprint('api', __name__, url_prefix='/api')

# Inicializa handler do MongoDB
db_handler = None

def get_db_handler():
    """Retorna instância do MongoDBHandler (lazy loading)"""
    global db_handler
    if db_handler is None:
        try:
            db_handler = MongoDBHandler()
        except Exception as e:
            logger.error(f"Erro ao inicializar MongoDB: {str(e)}")
            return None
    return db_handler

@api_routes.route('/oportunidades', methods=['GET'])
def get_oportunidades():
    """Endpoint para listar oportunidades (editais + vagas) com filtros"""
    db = get_db_handler()

    # Fallback para dados mockados se MongoDB não estiver disponível
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
def get_editais():
    """Endpoint para listar editais com filtros"""
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
def get_vagas():
    """Endpoint para listar vagas com filtros"""
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
    """Endpoint para listar notícias com filtros"""
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


@api_routes.route('/oportunidades/<int:id>', methods=['GET'])
def get_oportunidade_by_id(id):
    """Endpoint para buscar oportunidade por ID"""
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
