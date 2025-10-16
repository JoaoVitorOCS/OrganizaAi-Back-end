from flask_restx import Api

def configure_swagger(app):
    """
    Configura o Swagger/OpenAPI para documentação da API
    """
    
    # Configuração do Swagger
    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Digite: Bearer &lt;seu_token_jwt&gt;'
        }
    }
    
    api = Api(
        app,
        version='1.0.0',
        title='API de Gestão de Gastos',
        description='''
        ## 📋 Sistema Inteligente de Gestão de Gastos
        
        API RESTful para gerenciamento inteligente de gastos pessoais com:
        - 🔐 Autenticação JWT
        - 📊 OCR para extração de dados
        - 🤖 IA para recomendações personalizadas
        - 📈 Dashboards interativos
        
        ### 🔑 Autenticação
        
        1. Registre-se em `/api/auth/register`
        2. Faça login em `/api/auth/login`
        3. Copie o `access_token` retornado
        4. Clique no botão **Authorize** 🔓 no topo
        5. Digite: `Bearer seu_token_aqui`
        6. Clique em **Authorize**
        7. Agora você pode testar os endpoints protegidos! ✅
        
        ### 📚 Documentação
        
        - **Swagger UI**: Documentação interativa (esta página)
        - **ReDoc**: Documentação alternativa em `/redoc`
        - **OpenAPI JSON**: Especificação em `/swagger.json`
        
        ### 🔗 Links Úteis
        
        - [GitHub](https://github.com/seu-usuario/OrganizaAi-Back-end)
        - [Documentação Completa](https://docs.exemplo.com)
        ''',
        doc='/docs',  # URL da documentação Swagger
        authorizations=authorizations,
        security='Bearer',
        contact='Sua Equipe',
        contact_email='contato@exemplo.com',
        license='MIT',
        prefix='/api'
    )
    
    return api