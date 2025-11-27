# Usa a imagem oficial CPU
FROM ghcr.io/docling-project/docling-serve-cpu:latest

WORKDIR /app

# 1. Atualiza o Docling (Isso é bom para pegar a correção do PPTX)
RUN pip install --upgrade docling

# 2. Configurações de Ambiente
# Habilita a UI e RAG
ENV DOCLING_SERVE_ENABLE_UI=true
ENV DOCLING_SERVE_ENABLE_RAG=true
# Define 0.0.0.0 para aceitar conexões externas
ENV HOST=0.0.0.0

# 3. Define um fallback para a porta (caso o Railway não injete, usa 5001)
ENV PORT=5001
EXPOSE $PORT

# 4. O COMANDO BLINDADO
# Removemos a cópia de requirements.txt pois a imagem base já tem tudo.
# Usamos 'sh -c' para que a variável ${PORT} seja lida corretamente do Railway.
CMD ["sh", "-c", "docling-serve run --host 0.0.0.0 --port ${PORT:-5001} --enable-ui"]
