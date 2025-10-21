import requests
import os
import base64

class GroqClient:
    """Cliente para integração com Groq API (Llama Vision)"""
    
    API_KEY = os.getenv("GROQ_API_KEY")
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Modelo com visão (GRATUITO)
    VISION_MODEL = "llama-3.2-11b-vision-preview"
    
    # Modelo de texto para classificação
    TEXT_MODEL = "llama-3.3-70b-versatile"
    
    @staticmethod
    def analyze_receipt_image(image_path: str) -> dict:
        """
        Analisa imagem de cupom fiscal e extrai dados estruturados.
        
        Args:
            image_path: Caminho para a imagem do cupom
            
        Returns:
            dict: Resposta da API Groq com dados extraídos
            
        Raises:
            ValueError: Se API key não estiver configurada ou erro na API
        """
        
        if not GroqClient.API_KEY:
            raise ValueError("GROQ_API_KEY não configurada no .env")
        
        print(f"📷 Analisando cupom: {os.path.basename(image_path)}")
        print(f"🤖 Modelo: {GroqClient.VISION_MODEL}")
        
        # Ler e codificar imagem em base64
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            
            print(f"📦 Tamanho da imagem: {len(image_bytes) / 1024:.2f} KB")
        except FileNotFoundError:
            raise ValueError(f"Arquivo não encontrado: {image_path}")
        except Exception as e:
            raise ValueError(f"Erro ao ler imagem: {e}")
        
        # Detectar tipo MIME da imagem
        ext = image_path.lower().split('.')[-1]
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Headers da requisição
        headers = {
            "Authorization": f"Bearer {GroqClient.API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prompt otimizado para extração de dados de cupom fiscal
        prompt = """
Analise cuidadosamente o cupom fiscal brasileiro na imagem e extraia as seguintes informações.

Retorne APENAS um objeto JSON válido no formato abaixo (sem markdown, sem explicações):

{
  "loja": "Nome completo do estabelecimento",
  "data_compra": "DD/MM/YYYY",
  "itens": [
    {
      "nome": "Nome do produto ou serviço",
      "quantidade": 1,
      "valor_unitario": 0.00,
      "valor_total": 0.00
    }
  ],
  "valor_total": 0.00,
  "forma_pagamento": "Débito/Crédito/Dinheiro/PIX/Outro",
  "categoria": null,
  "texto_bruto": "Todo o texto visível no cupom"
}

INSTRUÇÕES IMPORTANTES:
1. Extraia TODOS os itens/produtos listados no cupom
2. Valores devem ser números decimais com ponto (exemplo: 12.50)
3. Data no formato brasileiro DD/MM/YYYY
4. Para quantidade, se não especificado, use 1
5. Para valor_unitario e valor_total, se forem iguais, repita o valor
6. Se não conseguir identificar algum campo, use null
7. Em texto_bruto, transcreva todo o texto visível do cupom
8. Retorne APENAS o JSON, sem ```json, sem explicações antes ou depois
"""
        
        # Payload da requisição com imagem
        payload = {
            "model": GroqClient.VISION_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um especialista em interpretar cupons fiscais brasileiros. "
                        "Sua tarefa é extrair dados estruturados de forma precisa. "
                        "Sempre retorne JSON válido, sem formatação markdown."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,  # Baixa temperatura para respostas mais determinísticas
            "max_tokens": 2000,
            "top_p": 1,
            "stream": False
        }
        
        # Fazer requisição (APENAS UMA VEZ!)
        try:
            print("📤 Enviando para Groq API...")
            
            response = requests.post(
                GroqClient.API_URL,
                headers=headers,
                json=payload,
                timeout=90  # 90 segundos para processamento de imagem
            )
            
            # Verificar erros HTTP
            if response.status_code == 401:
                raise ValueError(
                    "API Key inválida ou expirada. "
                    "Gere uma nova em: https://console.groq.com/keys"
                )
            
            if response.status_code == 429:
                raise ValueError(
                    "Limite de requisições atingido. "
                    "Plano gratuito: 30 req/min, 14400 req/dia. "
                    "Aguarde 1 minuto e tente novamente."
                )
            
            if response.status_code == 400:
                error_detail = response.json().get('error', {}).get('message', response.text)
                raise ValueError(f"Requisição inválida: {error_detail}")
            
            response.raise_for_status()
            
            # Parse da resposta
            result = response.json()
            
            # Verificar se há resposta válida
            if not result.get("choices") or not result["choices"]:
                raise ValueError("Resposta vazia da API Groq")
            
            # Informações de uso
            usage = result.get('usage', {})
            total_tokens = usage.get('total_tokens', 'N/A')
            
            print(f"✅ Análise concluída!")
            print(f"📊 Tokens usados: {total_tokens}")
            print(f"💰 Custo: $0.00 (gratuito)")
            
            return result
            
        except requests.exceptions.Timeout:
            raise ValueError(
                "Timeout ao processar imagem. "
                "A imagem pode ser muito grande ou a API está lenta. "
                "Tente com uma imagem menor (< 2MB)."
            )
            
        except requests.exceptions.ConnectionError:
            raise ValueError(
                "Erro de conexão com a API Groq. "
                "Verifique sua internet e tente novamente."
            )
            
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else 'N/A'
            error_text = e.response.text if e.response else str(e)
            raise ValueError(f"Erro HTTP {status} da API Groq: {error_text}")
            
        except Exception as e:
            print(f"❌ Erro inesperado: {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def classify_expense_category(items: list[dict]) -> str:
        """
        Classifica categoria de gasto baseado nos itens da compra.
        
        Args:
            items: Lista de itens do cupom
            
        Returns:
            str: Categoria classificada (Food, Transport, Utility, Entertainment)
        """
        
        if not GroqClient.API_KEY or not items:
            return "Utility"
        
        # Extrair nomes dos itens (máximo 10 para não exceder tokens)
        items_text = ", ".join([
            item.get('nome', '') 
            for item in items[:10] 
            if item.get('nome')
        ])
        
        if not items_text.strip():
            return "Utility"
        
        headers = {
            "Authorization": f"Bearer {GroqClient.API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
Classifique a seguinte lista de itens de compra em UMA das categorias abaixo:

Categorias disponíveis:
- Food (alimentos, bebidas, restaurantes, supermercado)
- Transport (combustível, transporte público, pedágio, estacionamento)
- Utility (contas, serviços, utilidades domésticas)
- Entertainment (lazer, diversão, streaming, jogos, cinema)

Itens comprados: {items_text}

Responda APENAS com o nome da categoria em inglês (Food, Transport, Utility ou Entertainment).
Não adicione explicações.
"""
        
        payload = {
            "model": GroqClient.TEXT_MODEL,  # Usa modelo de texto (mais rápido)
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um classificador de despesas que retorna apenas a categoria."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }
        
        try:
            response = requests.post(
                GroqClient.API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            # Extrair categoria
            category = response.json()["choices"][0]["message"]["content"].strip()
            
            # Validar categoria retornada
            valid_categories = ["Food", "Transport", "Utility", "Entertainment"]
            
            # Limpar resposta (remover pontuação, espaços extras)
            category_clean = category.strip().strip('.').strip()
            
            # Retornar se for válida
            if category_clean in valid_categories:
                return category_clean
            
            # Tentar encontrar a categoria na resposta
            for valid_cat in valid_categories:
                if valid_cat.lower() in category.lower():
                    return valid_cat
            
            # Se não encontrar, retornar padrão
            print(f"⚠️ Categoria inválida retornada: '{category}', usando 'Utility'")
            return "Utility"
            
        except Exception as e:
            print(f"⚠️ Erro ao classificar categoria: {type(e).__name__}: {str(e)}")
            return "Utility"