#!/usr/bin/env bash
# Uso: scripts/theme-push.sh <homolog|prod> [--publish]
# Requer: NUVEMSHOP_CLI_TOKEN, THEME_ID_HOMOLOG / THEME_ID_PROD no ambiente (ou .env)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
ENV_NAME="${1:?informe homolog ou prod}"
case "$ENV_NAME" in
  homolog) THEME_ID="${THEME_ID_HOMOLOG:?}";;
  prod)    THEME_ID="${THEME_ID_PROD:?}";;
  *) echo "ambiente inválido: $ENV_NAME"; exit 1;;
esac
TOKEN_FLAG=(); [ -n "${NUVEMSHOP_CLI_TOKEN:-}" ] && TOKEN_FLAG=(--token "$NUVEMSHOP_CLI_TOKEN")
cd theme
echo ">> diff ($ENV_NAME / theme $THEME_ID)"
nuvemshop theme diff --theme-id "$THEME_ID" "${TOKEN_FLAG[@]}"
echo ">> push"
nuvemshop theme push --theme-id "$THEME_ID" -y "${TOKEN_FLAG[@]}"
if [ "${2:-}" = "--publish" ]; then
  echo ">> publish"
  nuvemshop theme publish --theme-id "$THEME_ID" -y "${TOKEN_FLAG[@]}"
fi
