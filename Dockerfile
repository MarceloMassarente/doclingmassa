# Usa a imagem oficial CPU
FROM ghcr.io/docling-project/docling-serve-cpu:latest

WORKDIR /app

# --- AQUI ESTÁ O QUE VOCÊ PEDIU ---
# 1. Atualiza o Docling (corrige bugs recentes)
# 2. Instala o EasyOCR (para ter a opção de melhor qualidade)
# 3. Garante as libs do servidor (uvicorn/fastapi)
RUN pip install --no-cache-dir --upgrade docling easyocr uvicorn fastapi python-multipart

# Configurações de Ambiente para a UI
ENV HOST=0.0.0.0
ENV DOCLING_SERVE_ENABLE_UI=true
ENV DOCLING_SERVE_ENABLE_RAG=true

# Configuração da Porta (Dinâmica para o Railway)
EXPOSE $PORT

# --- COMANDO DE INICIALIZAÇÃO ---
# Inicia o servidor oficial (docling-serve) ouvindo na porta que o Railway mandar
CMD ["sh", "-c", "docling-serve run --host 0.0.0.0 --port ${PORT:-5001} --enable-ui"]
