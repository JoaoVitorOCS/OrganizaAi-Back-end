from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from app.config import Config
from app.routes.auth import auth_bp
from app.models.user import User

def create_app():
    """
    Factory pattern para criar a aplicação Flask
    Facilita testes e múltiplas instâncias
    """
    
    app = Flask(__name__)
    
    app.config.from_object(Config)
    
    jwt = JWTManager(app)
    
    with app.app_context():
        try:
            User.create_table()
            print("Banco de dados inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
    
    app.register_blueprint(auth_bp)
    
    # ==================== HANDLERS DE ERRO JWT ====================
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Executado quando o token está expirado"""
        return jsonify({
            'success': False,
            'message': 'Token expirado',
            'error': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Executado quando o token é inválido"""
        return jsonify({
            'success': False,
            'message': 'Token inválido',
            'error': 'invalid_token'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Executado quando o token não é fornecido"""
        return jsonify({
            'success': False,
            'message': 'Token de autenticação não fornecido',
            'error': 'authorization_required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Executado quando o token foi revogado"""
        return jsonify({
            'success': False,
            'message': 'Token revogado',
            'error': 'token_revoked'
        }), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        """Executado quando a verificação do token falha"""
        return jsonify({
            'success': False,
            'message': 'Falha na verificação do token',
            'error': 'token_verification_failed'
        }), 401
    
    # ==================== HANDLERS DE ERRO HTTP ====================
    
    @app.errorhandler(404)
    def not_found(error):
        """Rota não encontrada"""
        return jsonify({
            'success': False,
            'message': 'Rota não encontrada',
            'error': 'not_found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Método HTTP não permitido"""
        return jsonify({
            'success': False,
            'message': 'Método não permitido para esta rota',
            'error': 'method_not_allowed'
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Erro interno do servidor"""
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor',
            'error': 'internal_server_error'
        }), 500
    
    # ==================== ROTA DE HEALTH CHECK ====================
    
    @app.route('/')
    def home():
        """Rota raiz - health check"""
        return jsonify({
            'success': True,
            'message': 'API de OrganizaAí está funcionando!',
            'version': '1.0.0',
            'endpoints': {
                'auth': {
                    'register': 'POST /api/auth/register',
                    'login': 'POST /api/auth/login',
                    'profile': 'GET /api/auth/me',
                    'refresh': 'POST /api/auth/refresh',
                    'logout': 'POST /api/auth/logout'
                }
            }
        }), 200
    
    @app.route('/health')
    def health():
        """Health check para monitoramento"""
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected'
        }), 200
    
    return app