import os
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from services.file_handler import save_uploaded_file
from services.llm_client import analyze_receipt_image
from services.parser import parse_llm_response
from dotenv import load_dotenv

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
