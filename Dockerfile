FROM ghcr.io/docling-project/docling-serve-cpu:latest

WORKDIR /app

# --- A CORREÇÃO ESTÁ AQUI ---
# Forçamos a atualização do Docling para a versão mais recente
RUN pip install --upgrade docling

# Instala dependências extras (já fizemos isso antes, mas mantendo)
RUN pip install uvicorn fastapi python-multipart

# Usa a variável de ambiente $PORT (Boas práticas do Railway)
CMD uvicorn smart_main:app --host 0.0.0.0 --port $PORT
