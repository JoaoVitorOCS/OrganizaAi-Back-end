import json

def parse_llm_response(response: dict) -> dict:

    try:
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        return {
            "erro": f"Falha ao processar resposta da IA: {str(e)}",
            "raw": response
        }