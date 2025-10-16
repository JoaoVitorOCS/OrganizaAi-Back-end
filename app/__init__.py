from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config
from app.swagger import configure_swagger
from app.models.user import User

def create_app():
    """Factory pattern para criar a aplicação Flask"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # ==================== CONFIGURAR CORS ====================
    # Otimizado para React + Vercel/Netlify
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Cache-Control",
                "X-File-Name"
            ],
            "expose_headers": [
                "Content-Type",
                "Authorization",
                "X-Total-Count",
                "X-Page-Number"
            ],
            "supports_credentials": True,
            "max_age": 3600
        },
        # CORS para documentação Swagger também
        r"/docs": {
            "origins": "*",
            "methods": ["GET"]
        },
        r"/swagger.json": {
            "origins": "*",
            "methods": ["GET"]
        }
    })
    
    # Inicializar JWT
    jwt = JWTManager(app)
    
    # Configurar Swagger
    api = configure_swagger(app)
    
    # Importar namespaces
    from app.routes.auth import auth_ns
    from app.routes.ocr import ocr_ns
    
    # Registrar namespaces no Swagger
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(ocr_ns, path='/ocr')
    
    # Criar tabelas do banco
    with app.app_context():
        try:
            User.create_table()
            print("✅ Banco de dados inicializado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
    
    # ==================== HANDLERS DE ERRO JWT ====================
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'message': 'Token expirado',
            'error': 'token_expired'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {
            'success': False,
            'message': 'Token inválido',
            'error': 'invalid_token'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {
            'success': False,
            'message': 'Token de autenticação não fornecido',
            'error': 'authorization_required'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'message': 'Token revogado',
            'error': 'token_revoked'
        }, 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        return {
            'success': False,
            'message': 'Falha na verificação do token',
            'error': 'token_verification_failed'
        }, 401
    
    # ==================== HANDLERS DE ERRO HTTP ====================
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'message': 'Rota não encontrada',
            'error': 'not_found'
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            'success': False,
            'message': 'Método não permitido para esta rota',
            'error': 'method_not_allowed'
        }, 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return {
            'success': False,
            'message': 'Erro interno do servidor',
            'error': 'internal_server_error'
        }, 500
    
    # ==================== ROTA DE HEALTH CHECK ====================
    
    @app.route('/')
    def home():
        """Rota raiz - health check"""
        return {
            'success': True,
            'message': 'API de Gestão de Gastos',
            'version': '1.0.0',
            'docs': '/docs',
            'swagger_json': '/swagger.json',
            'cors_enabled': True
        }, 200
    
    @app.route('/health')
    def health():
        """Health check"""
        return {
            'success': True,
            'status': 'healthy',
            'database': 'connected'
        }, 200
    
    return app