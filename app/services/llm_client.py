import requests
import os
import base64
import json

try:
        import google.generativeai as genai  # type: ignore
except Exception:
        genai = None


class GeminiClient:
        """Cliente para integração com Gemini (Vision).

        Observações e suposições:
        - Este cliente tenta usar a biblioteca oficial `google-generative-ai` se instalada.
            Caso não esteja, o usuário receberá uma mensagem orientando a instalação.
        - É necessário configurar credenciais do Google: variável `GOOGLE_API_KEY` (API Key)
            ou `GOOGLE_APPLICATION_CREDENTIALS` (caminho para JSON de service account).
        - Mantive a interface pública compatível com o antigo cliente para não quebrar o
            restante do projeto: `analyze_receipt_image(image_path)` e
            `classify_expense_category(items)`.
        """

        # Preferência para API key em ambiente
        API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # Modelos padrão (ajuste via env se desejar)
        VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-mini-vision")
        TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-mini")

        # Endpoint REST fallback (usado apenas se a lib não estiver instalada)
        REST_BASE = "https://generativelanguage.googleapis.com/v1beta2"

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
        
            # Verificar credenciais
            if not GeminiClient.API_KEY and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                raise ValueError(
                    "Chave do Gemini/Google não configurada. Configure GOOGLE_API_KEY ou GOOGLE_APPLICATION_CREDENTIALS."
                )

            print(f"📷 Analisando cupom: {os.path.basename(image_path)}")
            print(f"🤖 Modelo (vision): {GeminiClient.VISION_MODEL}")
            
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
            # Prefer using the official library if available
            if genai is not None:
                try:
                    # Configure API key if provided
                    if GeminiClient.API_KEY:
                        genai.configure(api_key=GeminiClient.API_KEY)

                    # Construir mensagem multimodal: texto + image como data URI.
                    user_message = f"{prompt}\n\nImagem (data URI): data:{mime_type};base64,{image_base64}"

                    # Chamando a API de chat/assistente do GenAI
                    print("📤 Enviando para Gemini via google.generativeai...")
                    response = genai.chat.create(
                        model=GeminiClient.VISION_MODEL,
                        # content pode variar conforme versão da lib; usamos 'messages' estilo chat
                        messages=[
                            {"role": "system", "content": (
                                "Você é um especialista em interpretar cupons fiscais brasileiros. "
                                "Extraia dados estruturados e retorne apenas JSON válido."
                            )},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.1,
                    )

                    # Normalizar saída para o formato esperado pelo parser
                    # A biblioteca retorna uma estrutura com 'candidates' ou 'message'
                    # Vamos criar uma compatibilidade simples
                    content = ""
                    if isinstance(response, dict):
                        # tentar encontrar candidato de texto
                        content = response.get("candidates", [{}])[0].get("content", "") or response.get("message", {}).get("content", "")
                    else:
                        # objeto da lib: acessar message
                        content = getattr(response, 'last', None) or str(response)

                    result = {
                        "choices": [
                            {"message": {"content": content}}
                        ],
                        "raw": response
                    }

                    print("✅ Análise concluída (Gemini)")
                    return result

                except Exception as e:
                    print(f"❌ Erro ao chamar google.generativeai: {type(e).__name__}: {e}")
                    raise ValueError("Erro ao comunicar com Gemini; verifique credenciais e instalação da biblioteca.")

            # Se a biblioteca oficial não estiver disponível, usar REST mínimo via HTTP
            print("⚠️ Biblioteca google.generativeai não encontrada, usando fallback REST. Instale 'google-generative-ai' para melhor compatibilidade.")

            # Montar payload simples que envia o prompt + data URI da imagem no texto.
            # Nota: este fallback pode não suportar recursos multimodais avançados dependendo
            # do modelo/endpoint. Ajuste conforme necessidade.
            rest_model = GeminiClient.VISION_MODEL
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{rest_model}:generateContent?key={GeminiClient.API_KEY}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": mime_type, "data": image_base64}}
                        ]
                    }
                ]
            }

            try:
                resp = requests.post(endpoint, json=payload, timeout=90)
                resp.raise_for_status()
                data = resp.json()

                # Tentar mapear para formato compatível com parser
                content = ""
                if isinstance(data, dict):
                    # formas comuns: 'candidates' ou 'output' ou 'content'
                    if data.get('candidates'):
                        content = data['candidates'][0].get('output', '')
                    else:
                        content = json.dumps(data)

                result = {"choices": [{"message": {"content": content}}], "raw": data}
                return result

            except requests.exceptions.Timeout:
                raise ValueError("Timeout ao processar imagem no endpoint Gemini REST. Tente imagem menor (< 2MB).")
            except requests.exceptions.ConnectionError:
                raise ValueError("Erro de conexão com o endpoint Gemini REST. Verifique a internet.")
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else 'N/A'
                raise ValueError(f"Erro HTTP {status} da API Gemini: {e.response.text if e.response else str(e)}")
            except Exception as e:
                print(f"❌ Erro inesperado Gemini REST: {type(e).__name__}: {e}")
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
            if (not GeminiClient.API_KEY and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or not items:
                return "Utility"

            # Extrair nomes dos itens (máximo 10 para não exceder tokens)
            items_text = ", ".join([
                item.get('nome', '') 
                for item in items[:10] 
                if item.get('nome')
            ])

            if not items_text.strip():
                return "Utility"

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

            # Tentar usar a biblioteca oficial se presente
            if genai is not None:
                try:
                    if GeminiClient.API_KEY:
                        genai.configure(api_key=GeminiClient.API_KEY)

                    response = genai.chat.create(
                        model=GeminiClient.TEXT_MODEL,
                        messages=[
                            {"role": "system", "content": "Você é um classificador de despesas que retorna apenas a categoria."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_output_tokens=60
                    )

                    # Extrair texto da resposta
                    cat = ""
                    if isinstance(response, dict):
                        cat = response.get('candidates', [{}])[0].get('content', '') or response.get('message', {}).get('content', '')
                    else:
                        cat = str(response)

                    category = cat.strip()

                except Exception as e:
                    print(f"⚠️ Erro ao classificar com Gemini: {e}")
                    return "Utility"

            else:
                # Fallback REST mínimo
                rest_model = GeminiClient.TEXT_MODEL
                endpoint = f"{GeminiClient.REST_BASE}/models/{rest_model}:generate?key={GeminiClient.API_KEY}"
                payload = {"prompt": {"text": prompt}, "temperature": 0.1, "maxOutputTokens": 60}
                try:
                    r = requests.post(endpoint, json=payload, timeout=10)
                    r.raise_for_status()
                    data = r.json()
                    if data.get('candidates'):
                        category = data['candidates'][0].get('output', '')
                    else:
                        category = json.dumps(data)
                except Exception as e:
                    print(f"⚠️ Erro ao classificar via REST Gemini: {e}")
                    return "Utility"

            # Validar categoria retornada
            valid_categories = ["Food", "Transport", "Utility", "Entertainment"]
            category_clean = category.strip().strip('.').strip()
            if category_clean in valid_categories:
                return category_clean

            for valid_cat in valid_categories:
                if valid_cat.lower() in category.lower():
                    return valid_cat

            print(f"⚠️ Categoria inválida retornada: '{category}', usando 'Utility'")
            return "Utility"