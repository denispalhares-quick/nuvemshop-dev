# MCP server (Admin API + tools de tema). Usado pelo docker-compose.yml da raiz.
FROM python:3.11-slim

WORKDIR /app

# Node 20 + CLI da Nuvemshop: as tools theme_* chamam `nuvemshop` por baixo
ARG CLI_VERSION=2.3.0
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm i -g @tiendanube/cli@${CLI_VERSION} \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=2).raise_for_status()" || exit 1

CMD ["sh", "start.sh"]
