"""
Theme tools — embrulham a Nuvemshop CLI (@tiendanube/cli).

Requisitos:
  npm install -g @tiendanube/cli
  nuvemshop theme authorize        (uma vez, na máquina)  — ou NUVEMSHOP_CLI_TOKEN para CI

Env vars:
  THEME_DIR             pasta do tema (default: ../theme relativo a este arquivo)
  NUVEMSHOP_CLI_TOKEN   token para autenticação não interativa (--token)
  NUVEMSHOP_CLI_BIN     binário (default: nuvemshop)
"""
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

DEFAULT_THEME_DIR = Path(__file__).resolve().parent.parent.parent / "theme"


def _theme_dir() -> Path:
    return Path(os.getenv("THEME_DIR", str(DEFAULT_THEME_DIR))).resolve()


def _bin() -> str:
    return os.getenv("NUVEMSHOP_CLI_BIN", "nuvemshop")


def _run(args: list[str], json_output: bool = True, timeout: int = 600) -> dict[str, Any]:
    exe = shutil.which(_bin())
    if not exe:
        return {"error": f"CLI '{_bin()}' não encontrada. Instale com: npm install -g @tiendanube/cli"}
    cmd = [exe, "theme", *args]
    if json_output and "--json" not in cmd:
        cmd.append("--json")
    token = os.getenv("NUVEMSHOP_CLI_TOKEN")
    if token:
        cmd += ["--token", token]
    cwd = _theme_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout após {timeout}s", "cmd": " ".join(c for c in cmd if c != token)}
    out = proc.stdout.strip()
    result: dict[str, Any] = {
        "cmd": " ".join(c for c in cmd if c != token),
        "cwd": str(cwd),
        "returncode": proc.returncode,
    }
    try:
        result["data"] = json.loads(out) if out else None
    except json.JSONDecodeError:
        result["stdout"] = out
    if proc.stderr.strip():
        result["stderr"] = proc.stderr.strip()[-4000:]
    return result


def _theme_flag(theme_id: Optional[str]) -> list[str]:
    return ["--theme-id", str(theme_id)] if theme_id else []


def register(mcp):

    @mcp.tool()
    def theme_list() -> dict:
        """Lista as instalações de tema da loja (CLI: nuvemshop theme list)."""
        return _run(["list"])

    @mcp.tool()
    def theme_current() -> dict:
        """Mostra a instalação de tema vinculada à pasta local (.nuvem / manifest.json)."""
        return _run(["current"])

    @mcp.tool()
    def theme_pull(theme_id: Optional[str] = None, published: bool = False) -> dict:
        """Baixa os arquivos do tema para a pasta local (THEME_DIR). Use theme_id ou published=True para o tema publicado."""
        args = ["pull", *_theme_flag(theme_id), "-y"]
        if published:
            args.append("--published")
        return _run(args)

    @mcp.tool()
    def theme_diff(theme_id: Optional[str] = None, detailed: bool = False) -> dict:
        """Mostra o que um push enviaria, sem alterar nada. detailed=True inclui diffs unificados."""
        args = ["diff", *_theme_flag(theme_id)]
        if detailed:
            args.append("--detailed")
        return _run(args)

    @mcp.tool()
    def theme_push(confirm: bool = False, theme_id: Optional[str] = None, force: bool = False) -> dict:
        """Envia os arquivos locais para a instalação do tema. Exige confirm=True (rode theme_diff antes). force=True envia tudo sem comparar."""
        if not confirm:
            return {"error": "Operação de escrita. Rode theme_diff, revise e chame novamente com confirm=True."}
        args = ["push", *_theme_flag(theme_id), "-y"]
        if force:
            args.append("--force")
        return _run(args)

    @mcp.tool()
    def theme_publish(confirm: bool = False, theme_id: Optional[str] = None) -> dict:
        """Publica a instalação do tema como tema ativo da loja. Exige confirm=True."""
        if not confirm:
            return {"error": "Publicar troca o tema ativo da loja. Chame novamente com confirm=True."}
        return _run(["publish", *_theme_flag(theme_id), "-y"])

    @mcp.tool()
    def theme_preview(theme_id: Optional[str] = None) -> dict:
        """Retorna a URL de preview da instalação do tema."""
        return _run(["preview", *_theme_flag(theme_id)])

    @mcp.tool()
    def theme_performance(device: str = "mobile", detailed: bool = False) -> dict:
        """Roda a análise de performance do tema (device: mobile|desktop)."""
        args = ["performance", "--device", device]
        if detailed:
            args.append("--detailed")
        return _run(args, timeout=900)

    @mcp.tool()
    def theme_fork(confirm: bool = False) -> dict:
        """Faz fork da instalação atual para liberar edição completa do código do tema. Exige confirm=True."""
        if not confirm:
            return {"error": "Fork é irreversível sem unfork. Chame novamente com confirm=True."}
        return _run(["fork", "-y"])

    @mcp.tool()
    def theme_local_files(subdir: str = "") -> dict:
        """Lista os arquivos do tema na pasta local (sem chamar a CLI)."""
        base = _theme_dir() / subdir
        if not base.exists():
            return {"error": f"Pasta não existe: {base}"}
        files = sorted(str(p.relative_to(_theme_dir())) for p in base.rglob("*") if p.is_file() and ".git" not in p.parts)
        return {"theme_dir": str(_theme_dir()), "count": len(files), "files": files[:500]}
