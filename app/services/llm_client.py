import os

try:
        from google import genai  # type: ignore
        from google.genai.types import Content, Part  # type: ignore
except Exception:
        genai = None
        Content = None
        Part = None


class GeminiClient:
        """Cliente para integração com a API Gemini do Google.

        Observações:
        - Este cliente utiliza a biblioteca oficial `google-genai`.
        - É necessário configurar a API Key do Google na variável de ambiente `GOOGLE_API_KEY`.
        - A interface pública foi mantida para compatibilidade com o restante do projeto:
            `analyze_receipt_image(image_path)` e `classify_expense_category(items)`.
        """

        # Modelos padrão (podem ser sobrescritos via variáveis de ambiente)
        API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-1.5-pro-latest")
        TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash-latest")

        @classmethod
        def _ensure_library(cls) -> None:
            if not genai or Content is None or Part is None:
                raise ImportError(
                    "A biblioteca 'google-genai' não está instalada. "
                    "Instale-a com: pip install google-genai"
                )

        @classmethod
        def _create_client(cls) -> "genai.Client":
            cls._ensure_library()

            if not cls.API_KEY:
                raise ValueError("Chave da API do Google não configurada. Defina a variável de ambiente GOOGLE_API_KEY.")

            try:
                return genai.Client(api_key=cls.API_KEY)
            except Exception as exc:
                raise ValueError(
                    "Não foi possível inicializar o cliente Gemini. Verifique a chave de API e a instalação do pacote."
                ) from exc

        @staticmethod
        def analyze_receipt_image(image_path: str) -> dict:
            """
            Analisa a imagem de um cupom fiscal e extrai dados estruturados.

            Args:
                image_path: O caminho para o arquivo de imagem do cupom.

            Returns:
                Um dicionário contendo os dados extraídos no formato esperado pelo parser.

            Raises:
                ImportError: Se a biblioteca 'google-genai' não estiver instalada.
                ValueError: Se a API key não estiver configurada ou se ocorrer um erro na leitura
                            do arquivo ou na comunicação com a API.
            """
            client = GeminiClient._create_client()

            print(f"📷 Analisando cupom: {os.path.basename(image_path)}")
            print(f"🤖 Modelo (vision): {GeminiClient.VISION_MODEL}")

            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                print(f"📦 Tamanho da imagem: {len(image_bytes) / 1024:.2f} KB")
            except FileNotFoundError:
                raise ValueError(f"Arquivo não encontrado: {image_path}")
            except Exception as e:
                raise ValueError(f"Erro ao ler o arquivo de imagem: {e}")

            # Detecta o tipo MIME com base na extensão do arquivo
            ext = image_path.lower().split('.')[-1]
            mime_types = {
                'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                'webp': 'image/webp', 'gif': 'image/gif'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')

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
1. Extraia TODOS os itens/produtos listados no cupom.
2. Valores devem ser números decimais com ponto (exemplo: 12.50).
3. Data no formato brasileiro DD/MM/YYYY.
4. Para quantidade, se não especificado, use 1.
5. Para valor_unitario e valor_total, se forem iguais, repita o valor.
6. Se não conseguir identificar algum campo, use null.
7. Em texto_bruto, transcreva todo o texto visível do cupom.
8. Retorne APENAS o JSON, sem ```json, sem explicações antes ou depois.
"""
            try:
                print("📤 Enviando para a API Gemini...")
                contents = [
                    Content(
                        role="user",
                        parts=[
                            Part.from_text(prompt.strip()),
                            Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        ],
                    )
                ]
                response = client.models.generate_content(
                    model=GeminiClient.VISION_MODEL,
                    contents=contents,
                )

                # A resposta da biblioteca é encapsulada para manter a
                # compatibilidade com o resto do sistema que espera um formato específico.
                result = {
                    "choices": [{"message": {"content": response.text or ""}}],
                    "raw": str(response)  # Armazena a representação da resposta para debug
                }

                print("✅ Análise de imagem concluída.")
                return result

            except Exception as e:
                print(f"❌ Erro ao chamar a API Gemini: {type(e).__name__}: {e}")
                raise ValueError("Erro ao comunicar com a API Gemini. Verifique sua chave de API, o modelo configurado e a conexão.")

        @staticmethod
        def classify_expense_category(items: list[dict]) -> str:
            """
            Classifica a categoria de uma despesa com base em uma lista de itens.

            Args:
                items: Uma lista de dicionários, onde cada um representa um item da compra.

            Returns:
                A categoria classificada como uma string ('Food', 'Transport', etc.).
                Retorna 'Utility' como padrão em caso de erro ou falta de dados.
            """
            if not genai or Content is None or Part is None:
                print("⚠️ Biblioteca 'google-genai' não encontrada. A categoria não será classificada.")
                return "Utility"

            if not GeminiClient.API_KEY or not items:
                return "Utility"

            client = GeminiClient._create_client()

            # Concatena os nomes dos 10 primeiros itens para criar o prompt
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
            try:
                contents = [
                    Content(
                        role="user",
                        parts=[
                            Part.from_text(prompt.strip())
                        ],
                    )
                ]
                response = client.models.generate_content(
                    model=GeminiClient.TEXT_MODEL,
                    contents=contents,
                    generation_config={"temperature": 0.1, "max_output_tokens": 60}
                )
                category = (response.text or "").strip()

            except Exception as e:
                print(f"⚠️ Erro ao classificar categoria com a API Gemini: {e}")
                return "Utility"

            # Validação e limpeza da categoria retornada pela API
            valid_categories = ["Food", "Transport", "Utility", "Entertainment"]
            category_clean = category.strip().strip('.').strip()

            if category_clean in valid_categories:
                return category_clean

            # Fallback para caso a API retorne texto extra
            for valid_cat in valid_categories:
                if valid_cat.lower() in category.lower():
                    return valid_cat

            print(f"⚠️ Categoria inválida retornada pela API: '{category}'. Usando 'Utility' como padrão.")
            return "Utility"
