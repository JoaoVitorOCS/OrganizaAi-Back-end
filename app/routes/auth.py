from flask import Blueprint, request, jsonify
from app.models.user import User
from app.utils.jwt_handler import JWTHandler
from app.middleware.auth_middleware import token_required, get_current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """
    Valida força da senha
    
    Returns:
        (is_valid, message)
    """
    if len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    
    if len(password) > 100:
        return False, "Senha muito longa (máximo 100 caracteres)"
    
    return True, "Senha válida"


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Endpoint para registro de novos usuários
    
    Body JSON:
        {
            "email": "usuario@exemplo.com",
            "password": "senha123",
            "name": "João Silva"
        }
    
    Returns:
        201: Usuário criado com sucesso
        400: Dados inválidos
        409: Email já cadastrado
        500: Erro interno
    """
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Corpo da requisição vazio'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({
                'success': False,
                'message': 'Email, senha e nome são obrigatórios'
            }), 400
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Formato de email inválido'
            }), 400
        
        is_valid_password, password_message = validate_password(password)
        if not is_valid_password:
            return jsonify({
                'success': False,
                'message': password_message
            }), 400
        
        if len(name) < 3:
            return jsonify({
                'success': False,
                'message': 'Nome deve ter no mínimo 3 caracteres'
            }), 400
        
        existing_user = User.find_by_email(email)
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email já cadastrado'
            }), 409
        
        user = User.create_user(
            email=email,
            password=password,
            name=name
        )
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Erro ao criar usuário'
            }), 500
        
        tokens = JWTHandler.generate_tokens(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'data': {
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'created_at': user['created_at'].isoformat() if user.get('created_at') else None
                },
                'tokens': tokens
            }
        }), 201
        
    except Exception as e:
        print(f"Erro no registro: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuários
    
    Body JSON:
        {
            "email": "usuario@exemplo.com",
            "password": "senha123"
        }
    
    Returns:
        200: Login bem-sucedido
        400: Dados inválidos
        401: Credenciais incorretas
        500: Erro interno
    """
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Corpo da requisição vazio'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        user = User.find_by_email(email)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
        
        if not User.verify_password(password, user['password_hash']):
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
        
        tokens = JWTHandler.generate_tokens(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'data': {
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name']
                },
                'tokens': tokens
            }
        }), 200
        
    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor',
            'error': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_user_profile():
    """
    Endpoint protegido - retorna dados do usuário autenticado
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        200: Dados do usuário
        401: Token inválido
        404: Usuário não encontrado
        500: Erro interno
    """
    
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                'updated_at': user['updated_at'].isoformat() if user.get('updated_at') else None
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar perfil',
            'error': str(e)
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Endpoint para renovar access token usando refresh token
    
    Headers:
        Authorization: Bearer <refresh_token>
    
    Returns:
        200: Novo access token gerado
        401: Refresh token inválido
        404: Usuário não encontrado
        500: Erro interno
    """
    
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuário não encontrado'
            }), 404
        
        tokens = JWTHandler.generate_tokens(user['id'], user['email'])
        
        return jsonify({
            'success': True,
            'message': 'Token renovado com sucesso',
            'data': {
                'tokens': tokens
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao renovar token: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao renovar token',
            'error': str(e)
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    Endpoint para logout (informativo)
    
    Nota: JWT é stateless, então o logout real acontece no frontend
    descartando o token. Este endpoint apenas registra a ação.
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        200: Logout registrado
    """
    
    try:
        user = get_current_user()
        
        if user:
            print(f"Logout do usuário: {user['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Erro ao fazer logout',
            'error': str(e)
        }), 500