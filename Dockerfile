FROM ghcr.io/docling-project/docling-serve-cpu:latest

WORKDIR /app

# --- A CORREÇÃO ESTÁ AQUI ---
# Forçamos a atualização do Docling para a versão mais recente
RUN pip install --upgrade docling

# Instala dependências extras (já fizemos isso antes, mas mantendo)
RUN pip install uvicorn fastapi python-multipart

COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
# Habilita a Interface Gráfica (UI) e a API v2
ENV DOCLING_SERVE_ENABLE_UI=true
ENV DOCLING_SERVE_ENABLE_RAG=true


# Expõe a porta
EXPOSE 5001

# Comando oficial para iniciar com a UI e suporte a variáveis de ambiente
CMD ["sh", "-c", "docling-serve run --host 0.0.0.0 --port $PORT --enable-ui --no-show-header"]

# Usamos 'sh -c' para garantir que a variável $PORT do Railway seja lida.
CMD ["sh", "-c", "docling-serve run --host 0.0.0.0 --port $PORT --enable-ui"]
