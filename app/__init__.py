from flask import Flask
from flask_jwt_extended import JWTManager
from app.config import Config
from app.swagger import configure_swagger
from app.models.user import User

def create_app():
    """Factory pattern para criar a aplicação Flask"""
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar JWT
    jwt = JWTManager(app)
    
    # Configurar Swagger
    api = configure_swagger(app)
    
    # Importar namespaces (após configurar Swagger)
    from app.routes.auth import auth_ns
    
    # Registrar namespaces no Swagger
    api.add_namespace(auth_ns, path='/auth')
    
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
    
    # ==================== ROTA DE HEALTH CHECK ====================
    
    @app.route('/')
    def home():
        """Rota raiz - redireciona para documentação"""
        return {
            'success': True,
            'message': 'API de Gestão de Gastos',
            'version': '1.0.0',
            'docs': '/docs',
            'swagger_json': '/swagger.json'
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