import requests
import os
from typing import Optional
import base64

class GroqClient:
    """Cliente para integração com Groq API (Llama)"""
    
    API_KEY = os.getenv("GROQ_API_KEY")
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_NAME = "llama-3.3-70b-versatile"  # Modelo com visão integrada
    
    @staticmethod
    def analyze_receipt_image(image_path: str) -> dict:
        """
        Analisa imagem de cupom fiscal usando IA.
        
        Args:
            image_path: Caminho para a imagem do cupom
            
        Returns:
            dict: Resposta da API Groq
            
        Raises:
            ValueError: Se API key não estiver configurada
            requests.exceptions.HTTPError: Se a requisição falhar
        """
        if not GroqClient.API_KEY:
            raise ValueError("GROQ_API_KEY não configurada no .env")
        
        headers = {
            "Authorization": f"Bearer {GroqClient.API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prompt estruturado
        prompt = """
Analise o cupom fiscal da imagem fornecida e retorne APENAS um JSON válido no seguinte formato:

{
  "loja": "Nome do estabelecimento",
  "data_compra": "DD/MM/YYYY",
  "itens": [
    {
      "nome": "Nome do produto",
      "quantidade": 1,
      "valor_unitario": 0.00,
      "valor_total": 0.00
    }
  ],
  "valor_total": 0.00,
  "forma_pagamento": "Débito/Crédito/Dinheiro/PIX",
  "categoria": null,
  "texto_bruto": "Texto completo extraído do cupom"
}

IMPORTANTE:
- Retorne APENAS o JSON, sem texto adicional
- Valores devem ser números (float)
- Data no formato DD/MM/YYYY
- Se não conseguir identificar algum campo, use null
"""
        
        # Payload com imagem incluída
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        # 🔹 Agora sim o payload atualizado
        payload = {
            "model": GroqClient.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em interpretar cupons fiscais brasileiros com precisão. Retorne sempre JSON válido."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                GroqClient.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para Groq API: {e}")
            raise
        
        try:
            response = requests.post(
                GroqClient.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para Groq API: {e}")
            raise
    
    @staticmethod
    def classify_expense_category(items: list[dict]) -> str:
        """
        Classifica categoria de gasto baseado nos itens.
        
        Args:
            items: Lista de itens da compra
            
        Returns:
            str: Categoria classificada
        """
        if not GroqClient.API_KEY:
            return "Não Classificado"
        
        items_text = ", ".join([item.get('nome', '') for item in items])
        
        headers = {
            "Authorization": f"Bearer {GroqClient.API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
Classifique a seguinte lista de itens em UMA das categorias abaixo:

Categorias disponíveis:
- Food
- Transport
- Utility
- Entertainment

Itens: {items_text}

Retorne APENAS o nome da categoria, sem explicações.
"""
        
        payload = {
            "model": GroqClient.MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Você é um classificador de despesas."},
                {"role": "user", "content": prompt}
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
            category = response.json()["choices"][0]["message"]["content"].strip()
            return category
        except Exception as e:
            print(f"Erro ao classificar categoria: {e}")
            return "Não Classificado"