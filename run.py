from app import create_app
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from services.file_handler import save_uploaded_file
from services.llm_client import analyze_receipt_image
from services.parser import parse_llm_response
from dotenv import load_dotenv

app = create_app()

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print("=" * 60)
    print("Iniciando servidor Flask...")
    print(f"Host: {host}")
    print(f"Porta: {port}")
    print(f"Debug: {debug}")
    print(f"Acesse: http://localhost:{port}")
    print("=" * 60)
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )
    
    load_dotenv()

app = FastAPI(title="EconomizaAí - IA de Cupons")

@app.post("/analisar-cupom")
async def analisar_cupom(file: UploadFile = File(...)):
    try:

        file_path = save_uploaded_file(file, file.filename)

        llm_response = analyze_receipt_image(file_path)

        structured_data = parse_llm_response(llm_response)

        return JSONResponse(content=structured_data)

    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)