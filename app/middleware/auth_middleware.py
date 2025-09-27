from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models.user import User

def token_required(fn):
    """
    Decorator para proteger rotas que requerem autenticação
    
    Uso:
        @app.route('/rota-protegida')
        @token_required
        def minha_rota():
            ...
    """
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Token inválido ou expirado',
                'error': str(e)
            }), 401
    
    return wrapper


def get_current_user():
    """
    Retorna os dados do usuário autenticado a partir do token
    
    Returns:
        Dicionário com dados do usuário ou None se não encontrado
    """
    try:
        verify_jwt_in_request()
        
        jwt_data = get_jwt()
        user_id = jwt_data.get('sub')
        
        user = User.find_by_id(user_id)
        return user
        
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


def admin_required(fn):
    """
    Decorator para rotas que requerem privilégios de admin
    (Opcional - para implementação futura)
    
    Uso:
        @app.route('/admin/rota')
        @admin_required
        def rota_admin():
            ...
    """
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            
            user = get_current_user()
            
            if not user or not user.get('is_admin', False):
                return jsonify({
                    'success': False,
                    'message': 'Acesso negado: privilégios de administrador necessários'
                }), 403
            
            return fn(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Erro de autenticação',
                'error': str(e)
            }), 401
    
    return wrapper