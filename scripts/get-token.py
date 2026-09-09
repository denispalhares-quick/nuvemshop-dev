#!/usr/bin/env python3
"""
Troca o `code` do OAuth pelo access_token da loja.

Uso:
  1. Crie o app em https://www.nuvemshop.com.br/parceiros (anote App ID e Client Secret)
  2. Abra no navegador, logado como dono da loja:
       https://www.tiendanube.com/apps/<APP_ID>/authorize
  3. Após autorizar, a URL de redirect traz ?code=XXXX  (vale 5 minutos)
  4. python3 scripts/get-token.py --app-id <APP_ID> --secret <SECRET> --code <CODE>

Escreve TIENDANUBE_ACCESS_TOKEN e TIENDANUBE_STORE_ID no .env (use --print para só exibir).
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

TOKEN_URL = "https://www.tiendanube.com/apps/authorize/token"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def exchange(app_id: str, secret: str, code: str) -> dict:
    body = json.dumps({
        "client_id": app_id,
        "client_secret": secret,
        "grant_type": "authorization_code",
        "code": code,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def write_env(token: str, store_id: str) -> None:
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    values = {"TIENDANUBE_ACCESS_TOKEN": token, "TIENDANUBE_STORE_ID": store_id}
    seen = set()
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in values:
            out.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, val in values.items():
        if key not in seen:
            out.append(f"{key}={val}")
    ENV_PATH.write_text("\n".join(out) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Obtém o access_token da loja (OAuth Nuvemshop)")
    ap.add_argument("--app-id", required=True, help="App ID / client_id do app de parceiro")
    ap.add_argument("--secret", required=True, help="Client secret do app")
    ap.add_argument("--code", required=True, help="code retornado no redirect (expira em 5 min)")
    ap.add_argument("--print", action="store_true", help="só exibe, não escreve no .env")
    args = ap.parse_args()

    try:
        data = exchange(args.app_id, args.secret, args.code)
    except urllib.error.HTTPError as e:
        print(f"Erro {e.code}: {e.read().decode()[:500]}", file=sys.stderr)
        print("Dica: o `code` expira em 5 minutos — gere um novo abrindo a URL de authorize.", file=sys.stderr)
        return 1

    token, store_id = data.get("access_token"), str(data.get("user_id", ""))
    if not token:
        print(f"Resposta inesperada: {data}", file=sys.stderr)
        return 1

    print(f"access_token : {token}")
    print(f"store_id     : {store_id}")
    print(f"scopes       : {data.get('scope', '')}")
    if not args.print:
        write_env(token, store_id)
        print(f"\n-> gravado em {ENV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
