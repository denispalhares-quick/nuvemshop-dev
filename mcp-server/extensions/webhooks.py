"""
Webhooks — Nuvemshop Admin API (/webhooks)

Eventos suportados pela API (2025-03):
  app/uninstalled, app/suspended, app/resumed
  category/created, category/updated, category/deleted
  order/created, order/updated, order/paid, order/packed, order/fulfilled,
  order/cancelled, order/edited, order/pending, order/voided, order/unpacked
  product/created, product/updated, product/deleted
  product_variant/custom_fields_updated, product/custom_fields_updated
  domain/updated, store/redact, customers/redact, customers/data_request
  subscription/updated, fulfillment/updated
"""
from typing import Any, Callable, Optional

VALID_EVENTS = {
    "app/uninstalled", "app/suspended", "app/resumed",
    "category/created", "category/updated", "category/deleted",
    "order/created", "order/updated", "order/paid", "order/packed", "order/fulfilled",
    "order/cancelled", "order/edited", "order/pending", "order/voided", "order/unpacked",
    "product/created", "product/updated", "product/deleted",
    "product/custom_fields_updated", "product_variant/custom_fields_updated",
    "domain/updated", "store/redact", "customers/redact", "customers/data_request",
    "subscription/updated", "fulfillment/updated",
}


def register(mcp, make_request: Callable[..., Any]):

    @mcp.tool()
    def list_webhooks(page: int = 1, per_page: int = 50, event: Optional[str] = None, url: Optional[str] = None) -> list[dict]:
        """Lista os webhooks cadastrados na loja. Filtros opcionais: event (ex: order/paid) e url."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if event:
            params["event"] = event
        if url:
            params["url"] = url
        return make_request("GET", "/webhooks", params=params)

    @mcp.tool()
    def get_webhook(webhook_id: int) -> dict:
        """Obtém um webhook pelo ID."""
        return make_request("GET", f"/webhooks/{webhook_id}")

    @mcp.tool()
    def create_webhook(url: str, event: str) -> dict:
        """Cria um webhook. `url` deve ser HTTPS público; `event` no formato recurso/acao (ex: order/created, product/updated)."""
        if event not in VALID_EVENTS:
            return {"error": f"Evento inválido: {event}", "valid_events": sorted(VALID_EVENTS)}
        if not url.startswith("https://"):
            return {"error": "A URL do webhook precisa ser HTTPS."}
        return make_request("POST", "/webhooks", json_data={"url": url, "event": event})

    @mcp.tool()
    def update_webhook(webhook_id: int, url: Optional[str] = None, event: Optional[str] = None) -> dict:
        """Atualiza url e/ou event de um webhook existente."""
        data: dict[str, Any] = {}
        if url:
            data["url"] = url
        if event:
            if event not in VALID_EVENTS:
                return {"error": f"Evento inválido: {event}", "valid_events": sorted(VALID_EVENTS)}
            data["event"] = event
        if not data:
            return {"error": "Informe url e/ou event."}
        return make_request("PUT", f"/webhooks/{webhook_id}", json_data=data)

    @mcp.tool()
    def delete_webhook(webhook_id: int) -> dict:
        """Remove um webhook."""
        return make_request("DELETE", f"/webhooks/{webhook_id}")

    @mcp.tool()
    def list_webhook_events() -> list[str]:
        """Lista os eventos de webhook aceitos pela API da Nuvemshop."""
        return sorted(VALID_EVENTS)
