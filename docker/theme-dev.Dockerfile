# Imagem do serviço `theme` do docker-compose.yml: Node 20 + CLI da Nuvemshop.
# Não copia nada do repo — o código entra por volume, para editar no host.
FROM node:20-bookworm-slim

ARG CLI_VERSION=2.3.0
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/* \
    && npm i -g @tiendanube/cli@${CLI_VERSION} \
    && npm cache clean --force

WORKDIR /repo/theme
CMD ["nuvemshop", "--help"]
