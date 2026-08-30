#--- src/api/routes.py 

API Routes - Rotas da API RESTful

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cria blueprint para rotas da API
api_routes = Blueprint('api', __name__, url_prefix='/api')

# Dados mockados para desenvolvimento (serão substituídos pelo MongoDB)
MOCK_DATA = {
    'editais': [
        {
            'id': 1,
            'tipo': 'edital',
            'titulo': 'Bolsa de Iniciação Científica',
            'fonte': 'UERN',
            'url': 'https://uern.br/edital-001',
            'data_publicacao': '01/08/2026',
            'data_limite': '30/09/2026',
            'status': 'Aberto',
            'areas': ['Tecnologia', 'Exatas'],
            'valor': 'R$ 700,00'
        },
        {
            'id': 2,
            'tipo': 'edital',
            'titulo': 'Auxílio Permanência Estudantil',
            'fonte': 'JOUERN',
            'url': 'https://jouern.uern.br/edital-002',
            'data_publicacao': '15/08/2026',
            'data_limite': '15/09/2026',
            'status': 'Aberto',
            'areas': ['Saúde', 'Humanas'],
            'valor': 'R$ 400,00'
        }
    ],
    'vagas': [
        {
            'id': 1,
            'tipo': 'vaga_estagio',
            'titulo': 'Estagiário em Desenvolvimento Web',
            'fonte': 'CIEE',
            'empresa': 'Tech Solutions',
            'area': 'Tecnologia',
            'local': 'Natal/RN',
            'salario': 'R$ 1.200,00',
            'url': 'https://ciee.org.br/vaga-001'
        }
    ],
    'noticias': [
        {
            'id': 1,
            'tipo': 'noticia',
            'titulo': 'UERN lança novo laboratório de IA',
            'fonte': 'Portal UERN',
            'categoria': 'Tecnologia',
            'conteudo': 'Universidade inaugura espaço dedicado à pesquisa em Inteligência Artificial...',
            'url': 'https://uern.br/noticia-001',
            'data_publicacao': '20/08/2026'
        }
    ]
}
@api_routes.route('/oportunidades', methods=['GET'])
def get_oportunidades():
 
    args = request.args

    # Combina editais e vagas
    todas = MOCK_DATA['editais'] + MOCK_DATA['vagas']

    # Aplica filtros
    if args.get('area'):
        area = args.get('area').lower()
        todas = [i for i in todas if any(area in a.lower() for a in i.get('areas', [i.get('area', '')]))]

    if args.get('status'):
        status = args.get('status').capitalize()
        todas = [i for i in todas if i.get('status') == status or i.get('status') == 'Aberto']

    if args.get('tipo'):
        tipo = args.get('tipo').lower()
        todas = [i for i in todas if i.get('tipo') == tipo]

    logger.info(f"Retornando {len(todas)} oportunidades")
    return jsonify({
        'success': True,
        'count': len(todas),
        'data': todas
    })
@api_routes.route('/editais', methods=['GET'])
def get_editais():
   
    args = request.args
    editais = MOCK_DATA['editais'].copy()

    if args.get('status'):
        status = args.get('status').capitalize()
        editais = [e for e in editais if e.get('status') == status]

    if args.get('fonte'):
        fonte = args.get('fonte').upper()
        editais = [e for e in editais if fonte in e.get('fonte', '').upper()]

    logger.info(f"Retornando {len(editais)} editais")
    return jsonify({
        'success': True,
        'count': len(editais),
        'data': editais
    })
@api_routes.route('/vagas', methods=['GET'])
def get_vagas():
  
    args = request.args
    vagas = MOCK_DATA['vagas'].copy()

    if args.get('area'):
        area = args.get('area').lower()
        vagas = [v for v in vagas if area in v.get('area', '').lower()]

    logger.info(f"Retornando {len(vagas)} vagas")
    return jsonify({
        'success': True,
        'count': len(vagas),
        'data': vagas
    })
@api_routes.route('/noticias', methods=['GET'])
def get_noticias():
 
    args = request.args
    noticias = MOCK_DATA['noticias'].copy()

    if args.get('categoria'):
        categoria = args.get('categoria').lower()
        noticias = [n for n in noticias if categoria in n.get('categoria', '').lower()]

    logger.info(f"Retornando {len(noticias)} notícias")
    return jsonify({
        'success': True,
        'count': len(noticias),
        'data': noticias
    })


@api_routes.route('/oportunidades/<int:id>', methods=['GET'])
def get_oportunidade_by_id(id):
   
    todas = MOCK_DATA['editais'] + MOCK_DATA['vagas'] + MOCK_DATA['noticias']

    for item in todas:
        if item.get('id') == id:
            return jsonify({
                'success': True,
                'data': item
            })

    return jsonify({
        'success': False,
        'error': 'Oportunidade não encontrada'
    }), 404
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
