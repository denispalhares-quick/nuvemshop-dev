"""De onde vêm as imagens de cada produto, na ordem de prioridade:

1. coluna de imagens do CSV (URLs) -> enviadas como `src`;
2. pasta local (--images-dir): arquivos `<handle>.jpg`, `<handle>-2.jpg`, `<SKU>_1.png`...
   -> enviados em base64 (`attachment`) — não precisam estar publicados na internet;
3. placeholders (--placeholder-images): imagens de exemplo do próprio tema, via jsDelivr
   (útil para loja de demonstração sem fotos).

API: POST /products/{id}/images — .gif/.jpg/.png/.webp, até 10 MB, até 250 por produto.
"""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from pathlib import Path

from .csvfile import MAX_IMAGES, Product

EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_BYTES = 10 * 1024 * 1024
PLACEHOLDER_PATH = "theme/static/images/placeholders/products/product-{n}.webp"
PLACEHOLDER_COUNT = 8


@dataclass
class ImageSpec:
    label: str  # para o relatório (URL ou nome do arquivo)
    payload: dict  # corpo do POST /products/{id}/images (sem position/alt)


class ImageSource:
    def __init__(self, images_dir: str | Path | None = None, placeholder_base: str | None = None):
        self.images_dir = Path(images_dir) if images_dir else None
        self.placeholder_base = placeholder_base
        self._files = self._index_dir() if self.images_dir else {}

    def _index_dir(self) -> dict[str, list[Path]]:
        if not self.images_dir.is_dir():
            raise ValueError(f"pasta de imagens não encontrada: {self.images_dir}")
        index: dict[str, list[Path]] = {}
        for f in self.images_dir.iterdir():
            if f.suffix.lower() not in EXTENSIONS or not f.is_file():
                continue
            # "<chave>", "<chave>-2", "<chave>_02", "<chave> 3" -> chave
            key = re.sub(r"[-_ ]\d{1,3}$", "", f.stem).lower()
            index.setdefault(key, []).append(f)
        for files in index.values():
            files.sort(key=lambda f: _natural(f.stem))
        return index

    def for_product(self, product: Product, index: int) -> tuple[list[ImageSpec], list[str]]:
        """(imagens, problemas) para um produto. `index` escolhe o placeholder."""
        if product.images:
            return [ImageSpec(u, {"src": u}) for u in product.images[:MAX_IMAGES]], []

        if self._files:
            keys = [product.handle.lower()] + [v.sku.lower() for v in product.variants if v.sku]
            files = next((self._files[k] for k in keys if k in self._files), [])
            specs, problems = [], []
            for f in files[:MAX_IMAGES]:
                size = f.stat().st_size
                if size > MAX_BYTES:
                    problems.append(f"{f.name}: {size / 1024 / 1024:.1f} MB (máximo 10 MB)")
                    continue
                specs.append(ImageSpec(f.name, {
                    "attachment": base64.b64encode(f.read_bytes()).decode(),
                    "filename": f.name,
                }))
            if specs or problems:
                return specs, problems

        if self.placeholder_base:
            n = index % PLACEHOLDER_COUNT + 1
            url = f"{self.placeholder_base.rstrip('/')}/{PLACEHOLDER_PATH.format(n=n)}"
            return [ImageSpec(f"placeholder product-{n}", {"src": url})], []
        return [], []


def jsdelivr_base(repo_root: str | Path = ".") -> str | None:
    """https://cdn.jsdelivr.net/gh/<owner>/<repo>@<sha de origin/main> — lido do .git, sem o binário."""
    git = Path(repo_root) / ".git"
    config = (git / "config").read_text() if (git / "config").exists() else ""
    url = re.search(r'\[remote "origin"\][^[]*?url\s*=\s*(\S+)', config)
    repo = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url.group(1)) if url else None
    ref_file = git / "refs" / "remotes" / "origin" / "main"
    sha = ref_file.read_text().strip() if ref_file.exists() else None
    if not sha and (git / "packed-refs").exists():
        for line in (git / "packed-refs").read_text().splitlines():
            if line.endswith(" refs/remotes/origin/main"):
                sha = line.split()[0]
    if not (repo and sha):
        return None
    return f"https://cdn.jsdelivr.net/gh/{repo.group(1)}/{repo.group(2)}@{sha}"


def _natural(text: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]
