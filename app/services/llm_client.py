import requests
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

def analyze_receipt_image(image_path: str) -> dict:

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    files = {
        "file": ("receipt.jpg", image_bytes, "image/jpeg")
    }

    prompt = (
        "Interprete o cupom fiscal da imagem e me retorne um JSON no seguinte formato:\n"
        "{\n"
        "  'loja': string,\n"
        "  'data_compra': string,\n"
        "  'itens': [{'nome': string, 'valor': number}],\n"
        "  'valor_total': number,\n"
        "  'categoria': null,\n"
        "  'texto_bruto': string\n"
        "}"
    )

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Você é um assistente que interpreta cupons fiscais com precisão."},
            {"role": "user", "content": prompt}
        ],
    }

    response = requests.post(GROQ_API_URL, headers=headers, data={"model": MODEL_NAME}, files=files)
    response.raise_for_status()
    return response.json()