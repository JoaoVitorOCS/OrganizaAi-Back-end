from flask import request, make_response
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from app.middleware.auth_middleware import get_current_user
from app.services.file_handler import FileHandler
from app.services.llm_client import GeminiClient
from app.services.parser import ResponseParser
import os

# Criar namespace para OCR
ocr_ns = Namespace('ocr', description='Operações de OCR e análise de cupons fiscais')

# ==================== MODELS ====================

item_model = ocr_ns.model('Item', {
    'nome': fields.String(description='Nome do produto'),
    'quantidade': fields.Integer(description='Quantidade'),
    'valor_unitario': fields.Float(description='Valor unitário'),
    'valor_total': fields.Float(description='Valor total do item')
})

receipt_data_model = ocr_ns.model('ReceiptData', {
    'loja': fields.String(description='Nome do estabelecimento'),
    'data_compra': fields.String(description='Data da compra'),
    'itens': fields.List(fields.Nested(item_model)),
    'valor_total': fields.Float(description='Valor total da compra'),
    'forma_pagamento': fields.String(description='Forma de pagamento'),
    'categoria': fields.String(description='Categoria do gasto'),
    'arquivo': fields.String(description='Nome do arquivo')
})

upload_response_model = ocr_ns.model('OCRResponse', {
    'success': fields.Boolean(description='Status da operação'),
    'message': fields.String(description='Mensagem de retorno'),
    'data': fields.Nested(receipt_data_model)
})

error_model = ocr_ns.model('Error', {
    'success': fields.Boolean(description='Status da operação'),
    'message': fields.String(description='Mensagem de erro'),
    'error': fields.String(description='Detalhes do erro')
})

# ==================== ENDPOINTS ====================

@ocr_ns.route('/analyze')
class AnalyzeCoupon(Resource):
    
    # OPTIONS para preflight CORS
    def options(self):
        """Handle CORS preflight"""
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    @ocr_ns.doc('analyze_receipt',
                description='Analisa cupom fiscal/recibo usando OCR e IA (Gemini Vision)',
                security='Bearer',
                responses={
                    200: ('Análise concluída com sucesso', upload_response_model),
                    400: ('Arquivo inválido', error_model),
                    401: ('Não autenticado', error_model),
                    500: ('Erro interno', error_model)
                })
    @jwt_required()
    def post(self):
        """
        Analisar cupom fiscal ou recibo
        
        **Processo:**
        1. Upload do arquivo (PNG, JPG, JPEG, PDF)
        2. Extração de texto usando IA (Groq Llama)
        3. Estruturação dos dados
        4. Classificação automática da categoria
        5. Retorno dos dados estruturados
        
        **Requer autenticação via Bearer token**
        """
        try:
            # Verificar arquivo
            if 'file' not in request.files:
                return {
                    'success': False,
                    'message': 'Nenhum arquivo enviado',
                    'error': 'no_file'
                }, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {
                    'success': False,
                    'message': 'Nenhum arquivo selecionado',
                    'error': 'empty_filename'
                }, 400
            
            # Obter usuário autenticado
            user = get_current_user()
            if not user:
                return {
                    'success': False,
                    'message': 'Usuário não autenticado',
                    'error': 'unauthorized'
                }, 401
            
            # Salvar arquivo
            try:
                file_path, unique_filename = FileHandler.save_uploaded_file(file, user['id'])
            except ValueError as e:
                return {
                    'success': False,
                    'message': str(e),
                    'error': 'invalid_file_type'
                }, 400
            
            # Analisar com IA
            try:
                print(f"📄 Analisando cupom: {unique_filename}")
                llm_response = GeminiClient.analyze_receipt_image(file_path)
                
                # Parse da resposta
                # parsed_data = ResponseParser.parse_llm_response(llm_response)
                
                # if not parsed_data.get("success"):
                #     return {
                #         'success': False,
                #         'message': 'Erro ao processar resposta da IA',
                #         'error': parsed_data.get('error')
                #     }, 500
                
                # Classificar categoria se não veio da IA
                # data = parsed_data["data"]
                # if not data.get("categoria") or data["categoria"] == "Não Classificado":
                #     data["categoria"] = GeminiClient.classify_expense_category(data.get("itens", []))
                
                # Adicionar nome do arquivo
                # data["arquivo"] = unique_filename
                
                print(f"✅ Cupom analisado com sucesso: {llm_response}")
                
                return {
                    'success': True,
                    'message': 'Cupom analisado com sucesso',
                    'data': llm_response
                }, 200
                
            except ValueError as e:
                # Deletar arquivo se houver erro
                FileHandler.delete_file(file_path)
                return {
                    'success': False,
                    'message': str(e),
                    'error': 'groq_api_error'
                }, 500
                
            except Exception as e:
                # Deletar arquivo se houver erro
                FileHandler.delete_file(file_path)
                return {
                    'success': False,
                    'message': f'Erro ao processar arquivo: {str(e)}',
                    'error': 'processing_error'
                }, 500
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro inesperado: {str(e)}',
                'error': 'unexpected_error'
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
                description='Testa conectividade com Groq API',
                security='Bearer')
    @jwt_required()
    def get(self):
        """Testar configuração da API Gemini/Google"""
        gem_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        return {
            'success': True,
            'gemini_configured': bool(gem_key) or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
            'model': GeminiClient.VISION_MODEL,
            'cors_ok': True
        }, 200