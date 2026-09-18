"""Cliente mínimo da API da Nuvemshop (biblioteca padrão), com controle de rate limit.

A API usa balde (leaky bucket): x-rate-limit-limit (40), x-rate-limit-remaining e
x-rate-limit-reset (ms até esvaziar). Quando sobram poucas chamadas, o cliente espera;
em 429 e 5xx tenta de novo com backoff.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

DEFAULT_BASE_URL = "https://api.nuvemshop.com.br/2025-03"


class ApiError(Exception):
    def __init__(self, method: str, path: str, status: int, body: str):
        self.method, self.path, self.status, self.body = method, path, status, body
        super().__init__(f"{method} {path} -> HTTP {status}: {body[:500]}")


def load_env(path: str | Path = ".env") -> dict[str, str]:
    """Lê KEY=VALUE de um .env (ignora comentários, aspas e comentários no fim da linha)."""
    env: dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value and value[0] in "\"'" and value.count(value[0]) >= 2:
            value = value[1 : value.index(value[0], 1)]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        env[key] = value
    return env


class Client:
    def __init__(
        self,
        store_id: str,
        token: str,
        user_agent: str,
        base_url: str = DEFAULT_BASE_URL,
        min_remaining: int = 5,
        max_retries: int = 6,
        timeout: int = 60,
        sleep: Callable[[float], None] = time.sleep,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ):
        if not (store_id and token):
            raise ValueError("TIENDANUBE_STORE_ID e TIENDANUBE_ACCESS_TOKEN são obrigatórios (veja o .env)")
        self.base = f"{base_url.rstrip('/')}/{store_id}"
        self._headers = {
            "Authentication": f"bearer {token}",
            "User-Agent": user_agent or "nuvemshop-dev-catalog",
            "Content-Type": "application/json",
        }
        self.min_remaining = min_remaining
        self.max_retries = max_retries
        self.timeout = timeout
        self._sleep = sleep
        self._open = opener
        self.calls = 0

    def __repr__(self) -> str:  # nunca expor o token
        return f"Client({self.base!r})"

    @classmethod
    def from_env(cls, env_file: str | Path = ".env", **kwargs: Any) -> "Client":
        env = {**load_env(env_file), **{k: v for k, v in os.environ.items() if k.startswith("TIENDANUBE_")}}
        return cls(
            store_id=env.get("TIENDANUBE_STORE_ID", ""),
            token=env.get("TIENDANUBE_ACCESS_TOKEN", ""),
            user_agent=env.get("TIENDANUBE_USER_AGENT", ""),
            base_url=env.get("TIENDANUBE_BASE_URL") or DEFAULT_BASE_URL,
            **kwargs,
        )

    # -----------------------------------------------------------------------

    def request(self, method: str, path: str, body: Any = None, params: dict | None = None) -> Any:
        url = self.base + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None

        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(url, data=data, method=method, headers=self._headers)
            try:
                self.calls += 1
                with self._open(req, timeout=self.timeout) as resp:
                    payload = resp.read()
                    self._throttle(resp.headers)
                    return json.loads(payload) if payload else None
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", "replace")
                e.close()
                if e.code == 429 or e.code >= 500:
                    if attempt == self.max_retries:
                        raise ApiError(method, path, e.code, text) from None
                    reset_ms = _int(e.headers.get("x-rate-limit-reset")) if e.headers else None
                    self._sleep(max((reset_ms or 0) / 1000, 2 ** (attempt - 1)))
                    continue
                raise ApiError(method, path, e.code, text) from None
            except urllib.error.URLError:
                if attempt == self.max_retries:
                    raise
                self._sleep(2 ** (attempt - 1))
        raise RuntimeError("não deveria chegar aqui")

    def _throttle(self, headers: Any) -> None:
        remaining = _int(headers.get("x-rate-limit-remaining"))
        reset_ms = _int(headers.get("x-rate-limit-reset"))
        if remaining is not None and remaining <= self.min_remaining:
            self._sleep(min((reset_ms or 1000) / 1000, 20))

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, body: Any) -> Any:
        return self.request("POST", path, body=body)

    def put(self, path: str, body: Any) -> Any:
        return self.request("PUT", path, body=body)

    def get_all(self, path: str, params: dict | None = None, per_page: int = 200) -> list[Any]:
        """Todas as páginas. A Nuvemshop responde 404 para página além da última."""
        items: list[Any] = []
        page = 1
        while True:
            try:
                batch = self.get(path, {**(params or {}), "per_page": per_page, "page": page})
            except ApiError as e:
                if e.status == 404 and page > 1:
                    break
                raise
            items += batch or []
            if not batch or len(batch) < per_page:
                break
            page += 1
        return items


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
