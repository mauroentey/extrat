# api/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
from docx import Document
from PyPDF2 import PdfReader
import tempfile
from asgi_vercel import make_handler  # Importar make_handler

app = FastAPI()

# ... (el resto de tu código permanece igual)

# Al final del archivo, crea el manejador para Vercel
handler = make_handler(app)
