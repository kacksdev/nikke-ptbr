#!/usr/bin/env python3
"""Fail-closed audit for the public NIKKE PT-BR repository."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".7z", ".dll", ".exe", ".pdb", ".pyc", ".zip"}
FORBIDDEN_PARTS = {"__pycache__", "bin", "obj", "private", "work"}
TEXT_SUFFIXES = {
    ".cs",
    ".csproj",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".xaml",
    ".xml",
    ".yml",
    ".yaml",
}
SCREENSHOTS = (
    "01-lobby-ptbr.webp",
    "02-perfil-personagem-ptbr.webp",
    "03-dialogo-narrativo-ptbr.webp",
    "04-cena-historia-ptbr.webp",
    "05-escolhas-dialogo-ptbr.webp",
    "06-campanha-formacao-ptbr.webp",
    "07-progressao-recompensas-ptbr.webp",
    "08-inventario-item-ptbr.webp",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HTML_PATH = re.compile(r'(?:src|srcset)="([^"]+)"')


def tracked_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return tuple(
        ROOT / line
        for line in result.stdout.splitlines()
        if line and not line.startswith(".git/")
    )


def relative_target(source: Path, raw: str) -> Path | None:
    value = raw.strip().split(maxsplit=1)[0].strip("<>")
    if not value or value.startswith(("#", "https://", "http://", "mailto:")):
        return None
    path_text = value.split("#", 1)[0]
    if not path_text:
        return None
    return (source.parent / path_text).resolve(strict=False)


def main() -> int:
    files = tracked_files()
    errors: list[str] = []

    for path in files:
        relative = path.relative_to(ROOT)
        lowered_parts = {part.lower() for part in relative.parts}
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"artefato proibido: {relative.as_posix()}")
        if lowered_parts & FORBIDDEN_PARTS:
            errors.append(f"diretório privado ou gerado: {relative.as_posix()}")
        if not path.is_file():
            errors.append(f"arquivo listado ausente: {relative.as_posix()}")
            continue

        if path.suffix.lower() == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"JSON inválido em {relative.as_posix()}: {error}")

        if path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?i)[A-Z]:\\Users\\", text):
                errors.append(f"caminho pessoal exposto: {relative.as_posix()}")
            if path.suffix.lower() == ".md":
                for raw in (*MARKDOWN_LINK.findall(text), *HTML_PATH.findall(text)):
                    target = relative_target(path, raw)
                    if target is not None and not target.exists():
                        errors.append(
                            f"link local quebrado em {relative.as_posix()}: {raw}"
                        )

    screenshot_root = ROOT / "assets" / "screenshots"
    observed = tuple(
        path.name for path in sorted(screenshot_root.glob("*")) if path.is_file()
    )
    if observed != SCREENSHOTS:
        errors.append(
            "galeria divergente: esperado "
            + ", ".join(SCREENSHOTS)
            + "; encontrado "
            + ", ".join(observed)
        )

    if errors:
        for error in errors:
            print(f"ERRO: {error}")
        return 1

    print(f"Auditoria pública aprovada: {len(files)} arquivos, 8 capturas e 0 bloqueio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
