from flask import request, make_response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from app.middleware.auth_middleware import get_current_user
from app.services.file_handler import FileHandler
import os
from datetime import datetime, timedelta
import random
import string

# Criar namespace para OCR
ocr_ns = Namespace('ocr', description='Operações de OCR e análise de cupons fiscais')

# ==================== MODELS ====================

# ... (mantenha os models anteriores)

# ==================== FUNÇÕES AUXILIARES ====================

def generate_random_id(length=8):
    """Gera ID aleatório"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_mock_data():
    """Gera dados mockados no formato esperado pelo frontend"""
    
    # Lojas mockadas
    lojas = [
        "Supermercado Central",
        "Posto Shell",
        "Drogaria São Paulo",
        "McDonald's",
        "Carrefour",
        "Extra Hipermercado",
        "Farmácia Pague Menos"
    ]
    
    # Gerar dados para DataTableBackup_DataTableDemo (últimos gastos)
    gastos_recentes = []
    for i in range(10):
        days_ago = random.randint(0, 30)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        gastos_recentes.append({
            "id": generate_random_id(),
            "gastos": round(random.uniform(15.50, 950.00), 2),
            "status": random.choice(["success", "processing", "pending"]),
            "loja": random.choice(lojas),
            "date": date
        })
    
    # Ordenar por data (mais recente primeiro)
    gastos_recentes.sort(key=lambda x: x['date'], reverse=True)
    
    # Gerar dados para DataTableContainer (resumo)
    emails = [
        "user@example.com",
        "joao@example.com",
        "maria@example.com",
        "pedro@example.com"
    ]
    
    resumo_gastos = []
    for i in range(5):
        resumo_gastos.append({
            "id": generate_random_id(),
            "amount": random.randint(100, 1000),
            "status": random.choice(["success", "failed", "pending"]),
            "email": random.choice(emails)
        })
    
    # Gerar dados para ChartBarDefault (gastos mensais por categoria)
    meses = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    mes_atual = datetime.now().month
    
    chart_data = []
    for i in range(6):  # Últimos 6 meses
        mes_index = (mes_atual - i - 1) % 12
        mes = meses[mes_index]
        
        food = round(random.uniform(200, 600), 2)
        transport = round(random.uniform(100, 300), 2)
        utilities = round(random.uniform(80, 200), 2)
        entertainment = round(random.uniform(50, 150), 2)
        
        chart_data.append({
            "month": mes,
            "food": food,
            "transport": transport,
            "utilities": utilities,
            "entertainment": entertainment,
            "all": round(food + transport + utilities + entertainment, 2)
        })
    
    # Inverter para ordem cronológica
    chart_data.reverse()
    
    # Montar resposta final
    return {
        "tables": {
            "DataTableContainer": {
                "data": resumo_gastos
            },
            "DataTableBackup_DataTableDemo": {
                "data": gastos_recentes
            }
        },
        "charts": {
            "ChartBarDefault": {
                "data": chart_data
            }
        }
    }

# ==================== ENDPOINTS ====================

@ocr_ns.route('/dashboard')
class Dashboard(Resource):
    
    def options(self):
        """Handle CORS preflight"""
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @ocr_ns.doc('get_dashboard',
                description='Retorna dados mockados para dashboard (tabelas e gráficos)',
                security='Bearer',
                responses={
                    200: 'Dados do dashboard retornados com sucesso',
                    401: ('Não autenticado', error_model)
                })
    @jwt_required()
    def get(self):
        """
        Obter dados do dashboard (MOCKADO)
        
        Retorna dados formatados para:
        - DataTableContainer: Resumo de gastos
        - DataTableBackup_DataTableDemo: Últimos gastos detalhados
        - ChartBarDefault: Gráfico de barras mensal por categoria
        
        **Formato de resposta:**
```json
        {
          "tables": {
            "DataTableContainer": {
              "data": [...]
            },
            "DataTableBackup_DataTableDemo": {
              "data": [...]
            }
          },
          "charts": {
            "ChartBarDefault": {
              "data": [...]
            }
          }
        }
```
        """
        try:
            user = get_current_user()
            
            if not user:
                return {
                    'success': False,
                    'message': 'Usuário não autenticado'
                }, 401
            
            # Gerar dados mockados
            dashboard_data = generate_mock_data()
            
            print(f"📊 Dashboard mockado gerado para: {user['email']}")
            print(f"📋 Gastos recentes: {len(dashboard_data['tables']['DataTableBackup_DataTableDemo']['data'])}")
            print(f"📈 Meses no gráfico: {len(dashboard_data['charts']['ChartBarDefault']['data'])}")
            
            return dashboard_data, 200
            
        except Exception as e:
            print(f"❌ Erro ao gerar dashboard: {e}")
            return {
                'success': False,
                'message': f'Erro ao gerar dashboard: {str(e)}'
            }, 500


@ocr_ns.route('/analyze')
class AnalyzeCoupon(Resource):
    
    def options(self):
        """Handle CORS preflight"""
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    @ocr_ns.doc('analyze_receipt',
                description='Analisa cupom e adiciona aos dados mockados',
                security='Bearer')
    @jwt_required()
    def post(self):
        """
        Analisar cupom fiscal e adicionar ao dashboard
        
        Aceita upload de arquivo e simula adição aos dados do dashboard.
        """
        try:
            # Verificar arquivo
            if 'file' not in request.files:
                return {
                    'success': False,
                    'message': 'Nenhum arquivo enviado'
                }, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {
                    'success': False,
                    'message': 'Nenhum arquivo selecionado'
                }, 400
            
            user = get_current_user()
            if not user:
                return {
                    'success': False,
                    'message': 'Usuário não autenticado'
                }, 401
            
            # Salvar arquivo
            try:
                file_path, unique_filename = FileHandler.save_uploaded_file(file, user['id'])
            except ValueError as e:
                return {
                    'success': False,
                    'message': str(e)
                }, 400
            
            # Simular processamento
            import time
            time.sleep(1.5)
            
            # Gerar novo gasto mockado
            lojas = [
                "Supermercado Central",
                "Posto Shell", 
                "Drogaria São Paulo",
                "McDonald's",
                "Carrefour"
            ]
            
            novo_gasto = {
                "id": generate_random_id(),
                "gastos": round(random.uniform(25.00, 500.00), 2),
                "status": "success",
                "loja": random.choice(lojas),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "arquivo": unique_filename
            }
            
            print(f"✅ Novo gasto mockado: R$ {novo_gasto['gastos']:.2f} - {novo_gasto['loja']}")
            
            return {
                'success': True,
                'message': 'Cupom analisado com sucesso',
                'data': novo_gasto
            }, 200
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro: {str(e)}'
            }, 500


@ocr_ns.route('/test')
class TestOCR(Resource):
    
    def options(self):
        """Handle CORS preflight"""
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @ocr_ns.doc('test_ocr',
                description='Testa configuração da API',
                security='Bearer')
    @jwt_required()
    def get(self):
        """Testar status da API"""
        
        return {
            'success': True,
            'mode': 'MOCK',
            'message': 'API rodando com dados mockados',
            'endpoints': {
                'dashboard': 'GET /api/ocr/dashboard',
                'analyze': 'POST /api/ocr/analyze'
            }
        }, 200