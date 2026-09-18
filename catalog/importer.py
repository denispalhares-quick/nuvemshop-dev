"""Plano e execução da importação: categorias -> produtos (com variações) -> imagens.

- Idempotente: produto que já existe na loja (mesmo handle ou algum SKU) é pulado,
  ou atualizado com update=True. Imagens só são enviadas para produto sem imagens.
- dry_run=True só lê a loja (GET) e mostra o que faria.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .client import ApiError, Client
from .csvfile import SEO_DESCRIPTION_MAX, SEO_TITLE_MAX, Product, Variant
from .images import ImageSource

LANG = "pt"


@dataclass
class Outcome:
    handle: str
    name: str
    action: str  # criar | atualizar | pular | inválido | erro (com dry-run: planejado)
    product_id: int | None = None
    images: int = 0
    detail: str = ""


@dataclass
class Report:
    dry_run: bool
    categories_created: list[str] = field(default_factory=list)
    categories_reused: list[str] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)
    api_calls: int = 0

    def count(self, action: str) -> int:
        return sum(1 for o in self.outcomes if o.action == action)

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "api_calls": self.api_calls,
            "categories_created": self.categories_created,
            "categories_reused": self.categories_reused,
            "summary": {a: self.count(a) for a in ("criar", "atualizar", "pular", "inválido", "erro")},
            "images": sum(o.images for o in self.outcomes),
            "products": [o.__dict__ for o in self.outcomes],
        }


# ---------------------------------------------------------------------------
# payloads


def _ml(text: str) -> dict:
    return {LANG: text}


def variant_payload(v: Variant) -> dict:
    d: dict = {"price": v.price, "stock": v.stock if v.stock is not None else ""}
    if v.values:
        d["values"] = [_ml(x) for x in v.values]
    optional = {
        "promotional_price": v.promotional_price, "sku": v.sku, "barcode": v.barcode, "cost": v.cost,
        "weight": v.weight, "height": v.height, "width": v.width, "depth": v.depth,
    }
    d.update({k: val for k, val in optional.items() if val is not None})
    return d


def product_payload(p: Product, category_ids: list[int], with_variants: bool = True) -> dict:
    d: dict = {
        "name": _ml(p.name),
        "handle": _ml(p.handle),
        "description": _ml(p.description),
        "categories": category_ids,
        "visibility": p.visibility,  # não mandar `published` junto: a API responde 422
        "free_shipping": p.free_shipping,
        "requires_shipping": p.requires_shipping,
    }
    if p.brand:
        d["brand"] = p.brand
    if p.tags:
        d["tags"] = ", ".join(p.tags)
    if p.seo_title:
        d["seo_title"] = p.seo_title[:SEO_TITLE_MAX]
    if p.seo_description:
        d["seo_description"] = p.seo_description[:SEO_DESCRIPTION_MAX]
    if with_variants:
        if p.attributes:
            d["attributes"] = [_ml(a) for a in p.attributes]
        d["variants"] = [variant_payload(v) for v in p.variants]
    return d


# ---------------------------------------------------------------------------


class Importer:
    def __init__(
        self,
        client: Client,
        products: list[Product],
        *,
        invalid: set[str] = frozenset(),
        images: ImageSource | None = None,
        update: bool = False,
        dry_run: bool = True,
        log: Callable[[str], None] = print,
    ):
        self.client = client
        self.products = products
        self.invalid = invalid
        self.images = images
        self.update = update
        self.dry_run = dry_run
        self.log = log
        self.report = Report(dry_run=dry_run)
        self._categories: dict[tuple[int, str], int] = {}
        self._planned_id = 0

    # --- categorias -------------------------------------------------------

    def _load_categories(self) -> None:
        for c in self.client.get_all("/categories", {"fields": "id,name,parent"}):
            name = (c.get("name") or {}).get(LANG, "")
            self._categories[(c.get("parent") or 0, name.strip().lower())] = c["id"]

    def _category_path(self, path: list[str]) -> int:
        parent = 0
        for i, name in enumerate(path):
            key = (parent, name.strip().lower())
            label = " > ".join(path[: i + 1])
            if key in self._categories:
                if label not in self.report.categories_reused and label not in self.report.categories_created:
                    self.report.categories_reused.append(label)
            else:
                if self.dry_run:
                    self._planned_id -= 1
                    self._categories[key] = self._planned_id
                else:
                    body = {"name": _ml(name)}
                    if parent > 0:
                        body["parent"] = parent
                    self._categories[key] = self.client.post("/categories", body)["id"]
                self.report.categories_created.append(label)
                self.log(f"  categoria {'(planejada)' if self.dry_run else 'criada'}: {label}")
            parent = self._categories[key]
        return parent

    # --- produtos existentes ----------------------------------------------

    def _load_products(self) -> tuple[dict[str, dict], dict[str, dict]]:
        by_handle: dict[str, dict] = {}
        by_sku: dict[str, dict] = {}
        for p in self.client.get_all("/products", {"fields": "id,handle,variants,images"}):
            by_handle[((p.get("handle") or {}).get(LANG) or "").lower()] = p
            for v in p.get("variants") or []:
                if v.get("sku"):
                    by_sku[v["sku"].lower()] = p
        return by_handle, by_sku

    # --- execução -----------------------------------------------------------

    def run(self) -> Report:
        mode = "DRY-RUN (nada é gravado)" if self.dry_run else "APLICANDO na loja"
        self.log(f"== {mode}: {len(self.products)} produto(s)")
        self._load_categories()
        by_handle, by_sku = self._load_products()

        for index, p in enumerate(self.products):
            if p.handle in self.invalid:
                self.report.outcomes.append(Outcome(p.handle, p.name, "inválido", detail="erros de validação"))
                continue
            existing = by_handle.get(p.handle.lower()) or next(
                (by_sku[v.sku.lower()] for v in p.variants if v.sku and v.sku.lower() in by_sku), None
            )
            try:
                outcome = self._import_one(p, index, existing)
            except ApiError as e:
                outcome = Outcome(p.handle, p.name, "erro", detail=f"HTTP {e.status}: {e.body[:300]}")
            self.report.outcomes.append(outcome)
            if outcome.action in ("erro",) or (index + 1) % 10 == 0 or index + 1 == len(self.products):
                self.log(f"  [{index + 1}/{len(self.products)}] {outcome.action}: {p.handle}"
                         + (f" — {outcome.detail}" if outcome.detail else ""))

        self.report.api_calls = self.client.calls
        return self.report

    def _import_one(self, p: Product, index: int, existing: dict | None) -> Outcome:
        category_ids = [self._category_path(path) for path in p.categories if path]
        image_specs, image_problems = self.images.for_product(p, index) if self.images else ([], [])
        detail = "; ".join(image_problems)

        if existing and not self.update:
            return Outcome(p.handle, p.name, "pular", existing["id"], detail="já existe na loja")

        if self.dry_run:
            action = "atualizar" if existing else "criar"
            has_images = bool(existing and existing.get("images"))
            planned_images = 0 if has_images else len(image_specs)
            return Outcome(p.handle, p.name, action, existing["id"] if existing else None, planned_images, detail)

        if existing:
            pid = existing["id"]
            self.client.put(f"/products/{pid}", product_payload(p, category_ids, with_variants=False))
            self._update_variants(pid, p, existing.get("variants") or [])
            action, has_images = "atualizar", bool(existing.get("images"))
        else:
            created = self.client.post("/products", product_payload(p, category_ids))
            pid, action, has_images = created["id"], "criar", False

        sent = 0
        if not has_images:
            for position, spec in enumerate(image_specs, start=1):
                try:
                    self.client.post(f"/products/{pid}/images", {**spec.payload, "position": position, "alt": p.name})
                    sent += 1
                except ApiError as e:
                    detail = "; ".join(filter(None, [detail, f"imagem {spec.label}: HTTP {e.status}"]))
        return Outcome(p.handle, p.name, action, pid, sent, detail)

    def _update_variants(self, pid: int, p: Product, current: list[dict]) -> None:
        by_sku = {(v.get("sku") or "").lower(): v for v in current if v.get("sku")}
        by_values = {tuple((x or {}).get(LANG, "") for x in v.get("values") or []): v for v in current}
        for v in p.variants:
            match = (by_sku.get(v.sku.lower()) if v.sku else None) or by_values.get(tuple(v.values))
            body = variant_payload(v)
            if match:
                body.pop("values", None)
                self.client.put(f"/products/{pid}/variants/{match['id']}", body)
            else:
                self.client.post(f"/products/{pid}/variants", body)
