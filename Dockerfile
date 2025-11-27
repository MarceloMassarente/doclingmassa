FROM ghcr.io/docling-project/docling-serve-cpu:latest

WORKDIR /app

# Copia o script modificado
COPY app_override.py /app/smart_main.py

# Instala dependências extras se necessário (FastAPI já vem, mas garanta uvicorn)
# A imagem base já deve ter, mas por segurança:
RUN pip install uvicorn fastapi python-multipart

ENV PORT=8080
EXPOSE 8080

# Comando para rodar o NOSSO script, não o original
CMD ["uvicorn", "smart_main:app", "--host", "0.0.0.0", "--port", "8080"]
