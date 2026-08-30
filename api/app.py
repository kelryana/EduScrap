#--- src/api/app.py

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()
def create_app():

    app = Flask(__name__)

    # Configurações
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Habilita CORS para permitir requisições do front-end
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Registra rotas
    from .routes import api_routes
    app.register_blueprint(api_routes)

    # Rota de health check
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'EduScrap API',
            'version': '1.0'
        })

    # Rota root
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Bem-vindo à API EduScrap',
            'endpoints': {
                'oportunidades': '/api/oportunidades',
                'editais': '/api/editais',
                'vagas': '/api/vagas',
                'noticias': '/api/noticias',
                'health': '/health'
            }
        })

    logger.info("Aplicação Flask criada com sucesso")
    return app


if __name__ == '__main__':
    app = create_app()

    # Obtém configurações do ambiente
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'

    logger.info(f"Iniciando servidor em http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
