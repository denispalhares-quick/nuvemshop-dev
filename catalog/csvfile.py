"""Leitura e validação do CSV de produtos no formato de importação/exportação da Nuvemshop.

Cada linha é uma variação. A primeira linha de um "Identificador URL" traz os dados do
produto; as linhas seguintes com o mesmo identificador (e Nome vazio) são as outras
variações dele — é assim que o admin exporta produtos com tamanhos/cores.

Além das colunas padrão, aceita uma coluna opcional de imagens (qualquer cabeçalho que
contenha "imag", ex.: "Imagens") com URLs separadas por vírgula, espaço ou "|".
"""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

HANDLE = "Identificador URL"
NAME = "Nome"
CATEGORIES = "Categorias"
PRICE = "Preço"
REQUIRED_COLUMNS = [HANDLE, NAME, PRICE]
UNSUPPORTED_COLUMNS = ["MPN (Cód. Exclusivo Modelo Fabricante)", "Sexo", "Faixa etária"]

SEO_TITLE_MAX = 70
SEO_DESCRIPTION_MAX = 320
MAX_ATTRIBUTES = 3
MAX_IMAGES = 250

HANDLE_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
IMAGE_HEADER_RE = re.compile(r"imag", re.I)
URL_SPLIT_RE = re.compile(r"[\s,|]+")
TRUE_VALUES = {"SIM", "S", "SI", "YES", "Y", "TRUE", "1", "VERDADEIRO"}


@dataclass
class Issue:
    level: str  # "erro" (produto não é importado) | "aviso" | "info"
    handle: str
    row: int
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] linha {self.row} ({self.handle or '-'}): {self.message}"


@dataclass
class Variant:
    row: int
    values: list[str]
    price: str | None
    promotional_price: str | None
    stock: int | None  # None = estoque ilimitado
    sku: str | None
    barcode: str | None
    weight: str | None
    height: str | None
    width: str | None
    depth: str | None
    cost: str | None


@dataclass
class Product:
    row: int
    handle: str
    name: str
    categories: list[list[str]]  # cada item é um caminho: ["Roupas", "Camisetas"]
    attributes: list[str]
    description: str
    tags: list[str]
    seo_title: str
    seo_description: str
    brand: str
    visibility: str  # visible | hidden | unlisted
    free_shipping: bool
    requires_shipping: bool
    images: list[str] = field(default_factory=list)
    unsupported: dict[str, str] = field(default_factory=dict)
    variants: list[Variant] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# conversões


def parse_number(value: str | None) -> str | None:
    """'59,90' / '59.90' / 'R$ 1.234,56' -> '59.90' / '1234.56'. Vazio -> None."""
    v = (value or "").strip().replace("R$", "").replace(" ", "")
    if not v:
        return None
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(",", ".")
    float(v)  # ValueError se não for número
    return v


def parse_bool(value: str | None, default: bool = False) -> bool:
    v = (value or "").strip().upper()
    return default if not v else v in TRUE_VALUES


def parse_visibility(raw: str | None, show_in_store: str | None) -> str:
    v = (raw or "").strip().lower()
    if "não list" in v or "nao list" in v or v == "unlisted":
        return "unlisted"
    if v.startswith("vis") or v == "visible":
        return "visible"
    if "ocult" in v or v == "hidden":
        return "hidden"
    return "visible" if parse_bool(show_in_store, default=True) else "hidden"


def split_list(value: str | None, sep: str = ",") -> list[str]:
    return [p.strip() for p in (value or "").split(sep) if p.strip()]


# ---------------------------------------------------------------------------
# leitura


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("não consegui decodificar o arquivo (UTF-8 / Windows-1252 / Latin-1)")


def read_csv(path: str | Path) -> list[Product]:
    text = _decode(Path(path).read_bytes())
    header = text.splitlines()[0] if text else ""
    delimiter = ";" if header.count(";") >= header.count(",") else ","
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    columns = [c.strip() for c in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"colunas obrigatórias ausentes: {', '.join(missing)} (separador detectado: {delimiter!r})")
    image_columns = [c for c in columns if IMAGE_HEADER_RE.search(c)]

    products: list[Product] = []
    by_handle: dict[str, Product] = {}
    for index, raw_row in enumerate(reader):
        row_no = index + 2  # +1 cabeçalho, +1 base 1
        row = {(k or "").strip(): (v or "").strip() for k, v in raw_row.items()}
        handle = row.get(HANDLE, "")
        product = by_handle.get(handle) if handle else None

        if product is None or row.get(NAME):
            if product is not None:
                product.parse_errors.append(
                    f"linha {row_no}: identificador repetido com Nome preenchido — tratada como variação"
                )
            else:
                product = _new_product(row, row_no, image_columns)
                products.append(product)
                if handle:
                    by_handle[handle] = product

        product.variants.append(_new_variant(row, row_no, product))
    return products


def _new_product(row: dict[str, str], row_no: int, image_columns: list[str]) -> Product:
    attributes = [row.get(f"Nome da variação {i}", "") for i in (1, 2, 3)]
    attributes = [a for a in attributes if a]
    images: list[str] = []
    for col in image_columns:
        images += [u for u in URL_SPLIT_RE.split(row.get(col, "")) if u]
    return Product(
        row=row_no,
        handle=row.get(HANDLE, ""),
        name=row.get(NAME, ""),
        categories=[split_list(path, ">") for path in split_list(row.get(CATEGORIES))],
        attributes=attributes,
        description=row.get("Descrição", ""),
        tags=split_list(row.get("Tags")),
        seo_title=row.get("Título para SEO", ""),
        seo_description=row.get("Descrição para SEO", ""),
        brand=row.get("Marca", ""),
        visibility=parse_visibility(row.get("Visibilidade"), row.get("Exibir na loja")),
        free_shipping=parse_bool(row.get("Frete gratis")),
        requires_shipping=parse_bool(row.get("Produto Físico"), default=True),
        images=images,
        unsupported={c: row[c] for c in UNSUPPORTED_COLUMNS if row.get(c)},
    )


def _new_variant(row: dict[str, str], row_no: int, product: Product) -> Variant:
    values = [row.get(f"Valor da variação {i}", "") for i in (1, 2, 3)][: len(product.attributes)]

    def number(column: str) -> str | None:
        try:
            return parse_number(row.get(column))
        except ValueError:
            product.parse_errors.append(f"linha {row_no}: {column} inválido ({row.get(column)!r})")
            return None

    stock_raw = row.get("Estoque", "")
    stock: int | None = None
    if stock_raw:
        try:
            stock = int(float(parse_number(stock_raw) or 0))
        except ValueError:
            product.parse_errors.append(f"linha {row_no}: Estoque inválido ({stock_raw!r})")

    return Variant(
        row=row_no,
        values=values,
        price=number(PRICE),
        promotional_price=number("Preço promocional"),
        stock=stock,
        sku=row.get("SKU") or None,
        barcode=row.get("Código de barras") or None,
        weight=number("Peso (kg)"),
        height=number("Altura (cm)"),
        width=number("Largura (cm)"),
        depth=number("Comprimento (cm)"),
        cost=number("Custo"),
    )


# ---------------------------------------------------------------------------
# validação


def validate(products: list[Product]) -> list[Issue]:
    issues: list[Issue] = []
    sku_count = Counter(v.sku for p in products for v in p.variants if v.sku)
    handle_count = Counter(p.handle for p in products if p.handle)

    for p in products:
        def add(level: str, message: str, row: int | None = None) -> None:
            issues.append(Issue(level, p.handle, row or p.row, message))

        for message in p.parse_errors:
            add("erro", message)
        if not p.handle:
            add("erro", "Identificador URL vazio")
        elif not HANDLE_RE.fullmatch(p.handle):
            add("aviso", "Identificador URL fora do padrão (minúsculas, números e hífens) — a loja pode ajustá-lo")
        if handle_count[p.handle] > 1:
            add("erro", "Identificador URL usado por mais de um produto")
        if not p.name:
            add("erro", "Nome vazio")
        if len(p.attributes) > MAX_ATTRIBUTES:
            add("erro", f"mais de {MAX_ATTRIBUTES} variações por produto")
        if not p.categories:
            add("aviso", "sem categoria")
        if len(p.seo_title) > SEO_TITLE_MAX:
            add("aviso", f"Título para SEO com {len(p.seo_title)} caracteres — será cortado em {SEO_TITLE_MAX}")
        if len(p.seo_description) > SEO_DESCRIPTION_MAX:
            add("aviso", f"Descrição para SEO com {len(p.seo_description)} caracteres — será cortada em {SEO_DESCRIPTION_MAX}")
        if len(p.images) > MAX_IMAGES:
            add("erro", f"{len(p.images)} imagens — máximo {MAX_IMAGES}")
        for url in p.images:
            if not url.lower().startswith(("http://", "https://")):
                add("erro", f"imagem não é URL http(s): {url}")
        for column, value in p.unsupported.items():
            add("info", f"'{column}' ({value}) não é enviado — a API de produtos não tem esse campo")

        seen_values: set[tuple[str, ...]] = set()
        for v in p.variants:
            if p.attributes and any(not x for x in v.values):
                add("erro", f"variação sem valor para {', '.join(p.attributes)}", v.row)
            key = tuple(v.values)
            if key in seen_values:
                add("erro", f"variação repetida: {' / '.join(v.values) or '(sem valores)'}", v.row)
            seen_values.add(key)
            if v.price is None:
                add("erro", "Preço vazio", v.row)
            elif v.promotional_price is not None and float(v.promotional_price) >= float(v.price):
                add("aviso", f"Preço promocional ({v.promotional_price}) não é menor que o Preço ({v.price})", v.row)
            if v.cost is not None and v.price is not None and float(v.cost) > float(v.price):
                add("aviso", f"Custo ({v.cost}) maior que o Preço ({v.price})", v.row)
            if v.sku and sku_count[v.sku] > 1:
                add("erro", f"SKU {v.sku} repetido no arquivo", v.row)

        if p.attributes and len(p.variants) == 1:
            add("info", f"variação '{', '.join(p.attributes)}' com um único valor "
                        f"({' / '.join(p.variants[0].values)}) — na loja vira um seletor de uma opção só")
    return issues


def invalid_handles(issues: list[Issue]) -> set[str]:
    return {i.handle for i in issues if i.level == "erro"}
