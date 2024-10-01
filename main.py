from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import tempfile
from docx import Document
from PyPDF2 import PdfReader
import requests  # Para descargar el archivo desde la URL

app = FastAPI()

def extract_text_docx(file_path: str) -> str:
    doc = Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

def extract_text_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text.append(extracted)
    return '\n'.join(text)

def extract_text_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def download_file(url: str, file_path: str):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
    else:
        raise HTTPException(status_code=400, detail="No se pudo descargar el archivo desde la URL proporcionada")

@app.post("/extract-text/")
async def extract_text(url: str = None, file: UploadFile = File(None)):
    allowed_extensions = ["docx", "pdf", "txt"]

    # Si se proporciona una URL, descargar el archivo
    if url:
        extension = url.split(".")[-1].lower()

        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado. Usa una URL que apunte a un .docx, .pdf o .txt")

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
                tmp_path = tmp.name
                download_file(url, tmp_path)

            # Extraer el texto según el tipo de archivo
            if extension == "docx":
                text = extract_text_docx(tmp_path)
            elif extension == "pdf":
                text = extract_text_pdf(tmp_path)
            elif extension == "txt":
                text = extract_text_txt(tmp_path)
            else:
                text = ""

            return JSONResponse(content={"text": text})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    # Si se proporciona un archivo subido
    elif file:
        filename = file.filename
        extension = filename.split(".")[-1].lower()

        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado. Usa .docx, .pdf o .txt")

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            # Extraer el texto según el tipo de archivo
            if extension == "docx":
                text = extract_text_docx(tmp_path)
            elif extension == "pdf":
                text = extract_text_pdf(tmp_path)
            elif extension == "txt":
                text = extract_text_txt(tmp_path)
            else:
                text = ""

            return JSONResponse(content={"text": text})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        raise HTTPException(status_code=400, detail="Debes proporcionar un archivo o una URL válida.")

# Punto de entrada para ejecutar la aplicación localmente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
