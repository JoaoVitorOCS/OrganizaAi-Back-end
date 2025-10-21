import json
import re
from typing import Optional

class ResponseParser:
    """Parser para respostas da IA"""
    
    @staticmethod
    def parse_llm_response(response: dict) -> dict:
        """
        Extrai e valida JSON da resposta do LLM
        
        Args:
            response: Resposta da API Groq
            
        Returns:
            dict: Dados estruturados do cupom
        """
        try:
           # Extrair conteúdo da resposta
            content = response.strip("`").replace("json\n", "").replace("\n```", "")
            # Parse do JSON
            parsed = json.loads(content)

            return {"success": True, "data": parsed, "raw_response": content}
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON inválido: {str(e)}",
                "raw_response": response.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
            
        except KeyError as e:
            return {
                "success": False,
                "error": f"Estrutura de resposta inválida: {str(e)}",
                "raw_response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar resposta: {str(e)}",
                "raw_response": response
            }
    
    @staticmethod
    def _validate_receipt_data(data: dict) -> dict:
        """
        Valida e normaliza dados do cupom
        
        Args:
            data: Dados parseados do JSON
            
        Returns:
            dict: Dados validados e normalizados
        """
        validated = {
            "loja": data.get("loja") or "Não identificado",
            "data_compra": data.get("data_compra") or None,
            "itens": [],
            "valor_total": 0.0,
            "forma_pagamento": data.get("forma_pagamento") or "Não identificado",
            "categoria": data.get("categoria") or "Não Classificado",
            "texto_bruto": data.get("texto_bruto") or ""
        }
        
        # Validar e normalizar itens
        items = data.get("itens", [])
        total = 0.0
        
        for item in items:
            try:
                valor = float(item.get("valor_total", 0) or item.get("valor", 0))
                validated["itens"].append({
                    "nome": item.get("nome", "Item desconhecido"),
                    "quantidade": int(item.get("quantidade", 1)),
                    "valor_unitario": float(item.get("valor_unitario", valor)),
                    "valor_total": valor
                })
                total += valor
            except (ValueError, TypeError):
                # Ignorar itens com valores inválidos
                continue
        
        # Usar valor total do cupom se disponível, senão somar itens
        validated["valor_total"] = float(data.get("valor_total", total) or total)
        
        return validated
    
    @staticmethod
    def format_for_database(parsed_data: dict, user_id: int, file_path: str) -> dict:
        """
        Formata dados para inserção no banco de dados
        
        Args:
            parsed_data: Dados parseados do cupom
            user_id: ID do usuário
            file_path: Caminho do arquivo
            
        Returns:
            dict: Dados formatados para o banco
        """
        data = parsed_data.get("data", {})
        
        return {
            "user_id": user_id,
            "loja": data.get("loja"),
            "data_compra": data.get("data_compra"),
            "valor_total": data.get("valor_total"),
            "categoria": data.get("categoria"),
            "forma_pagamento": data.get("forma_pagamento"),
            "itens": json.dumps(data.get("itens", [])),  # Serializar para JSON
            "texto_bruto": data.get("texto_bruto"),
            "arquivo_original": file_path,
            "processado_com_sucesso": parsed_data.get("success", False)
        }