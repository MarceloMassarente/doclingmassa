# app_override.py
import logging
import base64
import os
import tempfile
from io import BytesIO
from typing import List
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

# Imports do Docling
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# --- CONFIGURAÇÃO TURBINADA ---
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options.do_cell_matching = True
pipeline_options.generate_picture_images = True  # O Pulo do Gato: Habilita Crops
pipeline_options.images_scale = 2.0  # Zoom 2x para gráficos

# Instancia o conversor globalmente (Warm-up)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

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

# --- ENDPOINT NOVO ---
@app.post("/extract-smart", response_model=ExtractSmartResponse)
def extract_smart_endpoint(file: UploadFile = File(...)):
    # Salvar temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
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
            for element, _ in doc.iterate_items(page_no=page_no):
                if element.label == "picture":
                    bbox = element.prov[0].bbox
                    width = bbox.r - bbox.l
                    height = bbox.b - bbox.t
                    
                    # Filtro de tamanho (>150px)
                    if width > 150 and height > 150:
                        img = element.get_image(doc)
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        img_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                        
                        candidates.append(VisionCandidate(
                            ref_id=str(element.self_ref),
                            base64_image=img_str,
                            width=int(width), height=int(height)
                        ))
            
            output_slides.append(SlideData(
                page_number=page_no,
                markdown_content=md_text,
                vision_candidates=candidates
            ))

        return ExtractSmartResponse(filename=file.filename, slides=output_slides)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
