from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token, 
    get_jwt_identity,
    get_jwt
)
from datetime import datetime, timezone

class JWTHandler:
    """Classe para manipulação de tokens JWT"""
    
    @staticmethod
    def generate_tokens(user_id: int, email: str):
        """
        Gera par de tokens (access e refresh) para o usuário
        
        Args:
            user_id: ID único do usuário
            email: Email do usuário
            
        Returns:
            Dicionário com access_token, refresh_token e metadados
        """
        
        issued_at = datetime.now(timezone.utc).isoformat()
        
        access_additional_claims = {
            'email': email,
            'type': 'access',
            'issued_at': issued_at
        }
        
        refresh_additional_claims = {
            'type': 'refresh',
            'issued_at': issued_at
        }
        
        access_token = create_access_token(
            identity=user_id,
            additional_claims=access_additional_claims
        )
        
        refresh_token = create_refresh_token(
            identity=user_id,
            additional_claims=refresh_additional_claims
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    @staticmethod
    def get_current_user_id():
        """
        Extrai o ID do usuário do token JWT atual
        
        Returns:
            ID do usuário autenticado
        """
        return get_jwt_identity()
    
    @staticmethod
    def get_token_claims():
        """
        Retorna todas as claims do token atual
        
        Returns:
            Dicionário com as claims do JWT
        """
        return get_jwt()
    
    @staticmethod
    def get_user_email_from_token():
        """
        Extrai o email do usuário do token atual
        
        Returns:
            Email do usuário ou None
        """
        claims = get_jwt()
        return claims.get('email')