"""CLI: python3 -m catalog {validate,import} <arquivo.csv> [opções]"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .client import Client
from .csvfile import invalid_handles, read_csv, validate
from .images import ImageSource, jsdelivr_base
from .importer import Importer

REPORTS_DIR = Path("catalog/reports")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m catalog", description="Importa catálogo (CSV da Nuvemshop) para a loja.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="só valida o CSV (não acessa a loja)")
    v.add_argument("csv")
    v.add_argument("--show-info", action="store_true", help="lista também os avisos informativos")

    i = sub.add_parser("import", help="importa categorias, produtos e imagens (dry-run por padrão)")
    i.add_argument("csv")
    i.add_argument("--apply", action="store_true", help="grava na loja (sem isto, só mostra o plano)")
    i.add_argument("--update", action="store_true", help="atualiza produtos que já existem (handle ou SKU)")
    i.add_argument("--images-dir", help="pasta com imagens <handle>.jpg / <handle>-2.jpg / <SKU>.png")
    i.add_argument("--placeholder-images", action="store_true",
                   help="sem foto? usa as imagens de exemplo do tema (loja demo)")
    i.add_argument("--handle", action="append", default=[], help="importa só este(s) handle(s) (repetível)")
    i.add_argument("--limit", type=int, help="importa só os N primeiros produtos (teste)")
    i.add_argument("--env", default=".env", help="arquivo com as credenciais (padrão: .env)")
    i.add_argument("--show-info", action="store_true", help="lista também os avisos informativos")

    args = ap.parse_args(argv)

    try:
        products = read_csv(args.csv)
    except (OSError, ValueError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    issues = validate(products)
    _print_issues(products, issues, args.show_info)
    invalid = invalid_handles(issues)

    if args.cmd == "validate":
        return 1 if invalid else 0

    if args.handle:
        wanted = set(args.handle)
        products = [p for p in products if p.handle in wanted]
    if args.limit:
        products = products[: args.limit]

    placeholder_base = None
    if args.placeholder_images:
        placeholder_base = jsdelivr_base()
        if not placeholder_base:
            print("✗ --placeholder-images: não achei origin/main no .git para montar a URL do jsDelivr", file=sys.stderr)
            return 2
    try:
        images = ImageSource(args.images_dir, placeholder_base) if (args.images_dir or placeholder_base) else None
        client = Client.from_env(args.env)
    except ValueError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2

    report = Importer(client, products, invalid=invalid, images=images,
                      update=args.update, dry_run=not args.apply).run()
    _print_report(report)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"import-{datetime.now():%Y%m%d-%H%M%S}{'-dry-run' if report.dry_run else ''}.json"
    out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"relatório: {out}")
    if report.dry_run:
        print("nada foi gravado — rode de novo com --apply para importar")
    return 1 if report.count("erro") or invalid else 0


def _print_issues(products, issues, show_info: bool) -> None:
    variants = sum(len(p.variants) for p in products)
    counts = {lvl: sum(1 for i in issues if i.level == lvl) for lvl in ("erro", "aviso", "info")}
    print(f"CSV: {len(products)} produto(s), {variants} variação(ões) | "
          f"{counts['erro']} erro(s), {counts['aviso']} aviso(s), {counts['info']} info")
    shown = [i for i in issues if i.level != "info" or show_info]
    for issue in shown[:50]:
        print(f"  {issue}")
    if len(shown) > 50:
        print(f"  … e mais {len(shown) - 50}")
    if counts["info"] and not show_info:
        groups: dict[str, int] = {}
        for i in issues:
            if i.level == "info":
                key = i.message.split("(")[0].strip()
                groups[key] = groups.get(key, 0) + 1
        for key, n in groups.items():
            print(f"  [info] {n}x {key}… (--show-info para detalhes)")


def _print_report(report) -> None:
    s = report.to_dict()["summary"]
    verb = "planejado" if report.dry_run else "feito"
    print(f"\n== resumo ({verb}) — {report.api_calls} chamada(s) à API")
    print(f"  categorias: {len(report.categories_created)} nova(s) {report.categories_created or ''} "
          f"| {len(report.categories_reused)} existente(s) {report.categories_reused or ''}")
    print(f"  produtos: criar {s['criar']} | atualizar {s['atualizar']} | pular {s['pular']} "
          f"| inválido {s['inválido']} | erro {s['erro']}")
    print(f"  imagens: {sum(o.images for o in report.outcomes)}")
    for o in report.outcomes:
        if o.action == "erro" or (o.detail and o.action != "pular"):
            print(f"  ! {o.handle}: {o.action} — {o.detail}")


if __name__ == "__main__":
    sys.exit(main())
