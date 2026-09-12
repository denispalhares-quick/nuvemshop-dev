#!/usr/bin/env bash
# Gera o valor do secret NUVEMSHOP_CLI_TOKEN a partir do theme/.nuvem local.
#
# O `--token` da CLI espera Base64 de {"store_id": <número>, "access_token": "..."}
# (o mesmo que a página do `nuvemshop theme authorize` mostra). O theme/.nuvem
# guarda os mesmos dados em outro formato, então só convertemos.
#
# Uso (o token nunca aparece na tela):
#   scripts/cli-token.sh | gh secret set NUVEMSHOP_CLI_TOKEN
# Conferir antes de cadastrar:
#   (cd theme && nuvemshop theme list --token "$(../scripts/cli-token.sh)")
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f theme/.nuvem ] || { echo "theme/.nuvem não encontrado — rode 'nuvemshop theme authorize' dentro de theme/" >&2; exit 1; }

python3 - <<'PY'
import base64, json, sys
d = json.loads(base64.b64decode(open("theme/.nuvem").read()))
api = d.get("theme-api") or {}
store_id, token = api.get("storeId"), api.get("publicApiToken")
if not (store_id and token):
    sys.exit("theme/.nuvem sem theme-api.storeId/publicApiToken — rode 'nuvemshop theme authorize' de novo")
payload = json.dumps({"store_id": int(store_id), "access_token": token})
sys.stdout.write(base64.b64encode(payload.encode()).decode())
PY
