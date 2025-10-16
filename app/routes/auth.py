from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.utils.jwt_handler import JWTHandler
from app.middleware.auth_middleware import get_current_user
import re

# Criar namespace para autenticação
auth_ns = Namespace('auth', description='Operações de autenticação e gerenciamento de usuários')

# ==================== MODELS (SCHEMAS) ====================

# Model para registro de usuário
register_model = auth_ns.model('Register', {
    'email': fields.String(required=True, description='Email do usuário', example='usuario@exemplo.com'),
    'password': fields.String(required=True, description='Senha (mínimo 6 caracteres)', example='senha123'),
    'name': fields.String(required=True, description='Nome completo', example='João Silva')
})

# Model para login
login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='Email do usuário', example='usuario@exemplo.com'),
    'password': fields.String(required=True, description='Senha', example='senha123')
})

# Model de resposta de usuário
user_response_model = auth_ns.model('UserResponse', {
    'id': fields.Integer(description='ID do usuário'),
    'email': fields.String(description='Email do usuário'),
    'name': fields.String(description='Nome do usuário'),
    'created_at': fields.String(description='Data de criação')
})

# Model de tokens
tokens_model = auth_ns.model('Tokens', {
    'access_token': fields.String(description='Token de acesso JWT'),
    'refresh_token': fields.String(description='Token de renovação JWT'),
    'token_type': fields.String(description='Tipo do token', example='Bearer'),
    'expires_in': fields.Integer(description='Tempo de expiração em segundos', example=3600)
})

# Model de resposta de autenticação
auth_response_model = auth_ns.model('AuthResponse', {
    'success': fields.Boolean(description='Status da operação'),
    'message': fields.String(description='Mensagem de retorno'),
    'data': fields.Nested(auth_ns.model('AuthData', {
        'user': fields.Nested(user_response_model),
        'tokens': fields.Nested(tokens_model)
    }))
})

# Model de resposta de perfil
profile_response_model = auth_ns.model('ProfileResponse', {
    'success': fields.Boolean(description='Status da operação'),
    'data': fields.Nested(user_response_model)
})

# Model de resposta de erro
error_model = auth_ns.model('Error', {
    'success': fields.Boolean(description='Status da operação', example=False),
    'message': fields.String(description='Mensagem de erro'),
    'error': fields.String(description='Detalhes do erro')
})

# ==================== FUNÇÕES AUXILIARES ====================

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Valida força da senha"""
    if len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    if len(password) > 100:
        return False, "Senha muito longa (máximo 100 caracteres)"
    return True, "Senha válida"

# ==================== ENDPOINTS ====================

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register_user', 
                 description='Cria uma nova conta de usuário',
                 responses={
                     201: ('Usuário criado com sucesso', auth_response_model),
                     400: ('Dados inválidos', error_model),
                     409: ('Email já cadastrado', error_model),
                     500: ('Erro interno do servidor', error_model)
                 })
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.marshal_with(auth_response_model, code=201)
    def post(self):
        """Registrar novo usuário"""
        try:
            data = request.get_json()
            
            if not data:
                auth_ns.abort(400, 'Corpo da requisição vazio')
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            name = data.get('name', '').strip()
            
            if not email or not password or not name:
                auth_ns.abort(400, 'Email, senha e nome são obrigatórios')
            
            if not validate_email(email):
                auth_ns.abort(400, 'Formato de email inválido')
            
            is_valid_password, password_message = validate_password(password)
            if not is_valid_password:
                auth_ns.abort(400, password_message)
            
            if len(name) < 3:
                auth_ns.abort(400, 'Nome deve ter no mínimo 3 caracteres')
            
            existing_user = User.find_by_email(email)
            if existing_user:
                auth_ns.abort(409, 'Email já cadastrado')
            
            user = User.create_user(email=email, password=password, name=name)
            
            if not user:
                auth_ns.abort(500, 'Erro ao criar usuário')
            
            tokens = JWTHandler.generate_tokens(user['id'], user['email'])
            
            return {
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
            }, 201
            
        except Exception as e:
            auth_ns.abort(500, f'Erro interno: {str(e)}')


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_user',
                 description='Autenticar usuário e obter tokens JWT',
                 responses={
                     200: ('Login realizado com sucesso', auth_response_model),
                     400: ('Dados inválidos', error_model),
                     401: ('Credenciais inválidas', error_model),
                     500: ('Erro interno do servidor', error_model)
                 })
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.marshal_with(auth_response_model, code=200)
    def post(self):
        """Fazer login"""
        try:
            data = request.get_json()
            
            if not data:
                auth_ns.abort(400, 'Corpo da requisição vazio')
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                auth_ns.abort(400, 'Email e senha são obrigatórios')
            
            user = User.find_by_email(email)
            
            if not user:
                auth_ns.abort(401, 'Credenciais inválidas')
            
            if not User.verify_password(password, user['password_hash']):
                auth_ns.abort(401, 'Credenciais inválidas')
            
            tokens = JWTHandler.generate_tokens(user['id'], user['email'])
            
            return {
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
            }, 200
            
        except Exception as e:
            auth_ns.abort(500, f'Erro interno: {str(e)}')


@auth_ns.route('/me')
class Profile(Resource):
    @auth_ns.doc('get_profile',
                 description='Obter dados do usuário autenticado',
                 security='Bearer',
                 responses={
                     200: ('Perfil do usuário', profile_response_model),
                     401: ('Token inválido ou não fornecido', error_model),
                     404: ('Usuário não encontrado', error_model),
                     500: ('Erro interno do servidor', error_model)
                 })
    @auth_ns.marshal_with(profile_response_model, code=200)
    @jwt_required()
    def get(self):
        """Obter perfil do usuário autenticado"""
        try:
            user = get_current_user()
            
            if not user:
                auth_ns.abort(404, 'Usuário não encontrado')
            
            return {
                'success': True,
                'data': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                    'updated_at': user['updated_at'].isoformat() if user.get('updated_at') else None
                }
            }, 200
            
        except Exception as e:
            auth_ns.abort(500, f'Erro ao buscar perfil: {str(e)}')


@auth_ns.route('/refresh')
class Refresh(Resource):
    @auth_ns.doc('refresh_token',
                 description='Renovar access token usando refresh token',
                 security='Bearer',
                 responses={
                     200: ('Token renovado com sucesso', auth_ns.model('RefreshResponse', {
                         'success': fields.Boolean(),
                         'message': fields.String(),
                         'data': fields.Nested(auth_ns.model('RefreshData', {
                             'tokens': fields.Nested(tokens_model)
                         }))
                     })),
                     401: ('Refresh token inválido', error_model),
                     404: ('Usuário não encontrado', error_model),
                     500: ('Erro interno do servidor', error_model)
                 })
    @jwt_required(refresh=True)
    def post(self):
        """Renovar token de acesso"""
        try:
            current_user_id = get_jwt_identity()
            user = User.find_by_id(int(current_user_id))
            
            if not user:
                auth_ns.abort(404, 'Usuário não encontrado')
            
            tokens = JWTHandler.generate_tokens(user['id'], user['email'])
            
            return {
                'success': True,
                'message': 'Token renovado com sucesso',
                'data': {
                    'tokens': tokens
                }
            }, 200
            
        except Exception as e:
            auth_ns.abort(500, f'Erro ao renovar token: {str(e)}')


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout_user',
                 description='Fazer logout (informativo - JWT é stateless)',
                 security='Bearer',
                 responses={
                     200: ('Logout realizado', auth_ns.model('LogoutResponse', {
                         'success': fields.Boolean(),
                         'message': fields.String()
                     })),
                     401: ('Token inválido', error_model)
                 })
    @jwt_required()
    def post(self):
        """Fazer logout"""
        try:
            user = get_current_user()
            
            if user:
                print(f"ℹ️ Logout do usuário: {user['email']}")
            
            return {
                'success': True,
                'message': 'Logout realizado com sucesso'
            }, 200
            
        except Exception as e:
            auth_ns.abort(500, f'Erro ao fazer logout: {str(e)}')