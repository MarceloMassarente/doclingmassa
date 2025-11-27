import logging
import base64
import os
import tempfile
from io import BytesIO
from typing import List
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

# Imports do Docling
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# --- CONFIGURAÇÃO DEFENSIVA ---
# Tentamos importar as opções de PPTX. Se falhar, seguimos sem elas.
try:
    from docling.document_converter import PptxFormatOption
    HAS_PPTX_OPTIONS = True
except ImportError:
    print("AVISO: PptxFormatOption não disponível nesta versão. Usando padrão para PPTX.")
    HAS_PPTX_OPTIONS = False

# --- CONFIGURAÇÃO TURBINADA (Smart Vision) ---
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2.0

# Monta o dicionário de formatos
format_options = {
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
}

# Se a biblioteca suportar PPTX avançado, adicionamos. Se não, o padrão já resolve.
if HAS_PPTX_OPTIONS:
    format_options[InputFormat.PPTX] = PptxFormatOption(pipeline_options=pipeline_options)

# Instancia o conversor globalmente
doc_converter = DocumentConverter(format_options=format_options)

app = FastAPI()

# --- MODELOS ---
class VisionCandidate(BaseModel):
    ref_id: str
    base64_image: str
    width: int
    height: int

class SlideData(BaseModel):
    page_number: int
    markdown_content: str
    vision_candidates: List[VisionCandidate]

class ExtractSmartResponse(BaseModel):
    filename: str
    slides: List[SlideData]

# --- Rota de Saúde ---
@app.get("/")
def health_check():
    return {"status": "ok", "service": "smart-docling-cpu"}

# --- ENDPOINT PRINCIPAL ---
@app.post("/extract-smart", response_model=ExtractSmartResponse)
def extract_smart_endpoint(file: UploadFile = File(...)):
    # Detecta extensão para ajudar o Docling
    filename_lower = file.filename.lower()
    file_ext = ".pdf"
    if filename_lower.endswith(".pptx"):
        file_ext = ".pptx"
    elif filename_lower.endswith(".docx"):
        file_ext = ".docx"

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        # Converter
        result = doc_converter.convert(tmp_path)
        doc = result.document
        output_slides = []

        for page_no, page in doc.pages.items():
            # 1. Texto Base
            md_text = doc.export_to_markdown(page_no=page_no)
            
            # 2. Crops de Imagem
            candidates = []
            # Iteração segura que funciona para PDF e tenta funcionar para PPTX
            for element, _ in doc.iterate_items(page_no=page_no):
                if element.label == "picture":
                    # Verificações de segurança para evitar erros de NoneType
                    if hasattr(element, 'prov') and element.prov and element.prov[0].bbox:
                        bbox = element.prov[0].bbox
                        width = bbox.r - bbox.l
                        height = bbox.b - bbox.t
                        
                        # Filtro de tamanho
                        if width > 100 and height > 100:
                            try:
                                img = element.get_image(doc)
                                if img:
                                    buf = BytesIO()
                                    img.save(buf, format="PNG")
                                    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                                    
                                    candidates.append(VisionCandidate(
                                        ref_id=str(element.self_ref),
                                        base64_image=img_str,
                                        width=int(width), height=int(height)
                                    ))
                            except Exception:
                                # Se falhar ao extrair imagem (comum em PPTX vetorial), ignora e segue
                                pass
            
            output_slides.append(SlideData(
                page_number=page_no,
                markdown_content=md_text,
                vision_candidates=candidates
            ))

        return ExtractSmartResponse(filename=file.filename, slides=output_slides)

    except Exception as e:
        # Loga o erro mas retorna algo para não dar 500
        logging.error(f"Erro no processamento: {str(e)}")
        raise e

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
