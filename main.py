import os
import shutil
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from docx import Document
from PyPDF2 import PdfReader
import requests

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
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
        else:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar el archivo desde la URL proporcionada. Código de estado: {response.status_code}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error al intentar acceder a la URL: {str(e)}")

@app.post("/extract-text/")
async def extract_text(url: str = None, file: UploadFile = File(None)):
    allowed_extensions = ["docx", "pdf", "txt"]

    if url:
        extension = url.split(".")[-1].lower()

        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado. Usa una URL que apunte a un .docx, .pdf o .txt")

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=f".{extension}")
        os.close(tmp_fd)  # Cerrar el descriptor de archivo
        try:
            download_file(url, tmp_path)

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
            raise HTTPException(status_code=500, detail=f"Error inesperado al procesar el archivo desde la URL: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    elif file:
        filename = file.filename
        extension = filename.split(".")[-1].lower()

        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Tipo de archivo no soportado. Usa .docx, .pdf o .txt")

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        try:
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
            raise HTTPException(status_code=500, detail=f"Error inesperado al procesar el archivo subido: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        raise HTTPException(status_code=400, detail="Debes proporcionar un archivo o una URL válida.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
