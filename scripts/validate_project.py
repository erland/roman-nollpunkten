#!/usr/bin/env python3
"""Snabb deterministisk validering för Nollpunkten-projektet.

Använder endast Python-standardbiblioteket. Avsedd att kunna köras både
lokalt och i GitHub Actions.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

CHAPTER_RE = re.compile(r"kapitel-(\d{2})\.md$")
CHAPTER_H1_RE = re.compile(r"^#\s+Kapitel\s+(\d+)\s+[–-]\s+(.+?)\s*$")
MARKERS = ("TODO", "FIXME", "[PLACEHOLDER]")

REQUIRED_PATHS = (
    "README.md",
    "roman-bibel.md",
    "synopsis.md",
    "kapitelplan.md",
    "projektstatus.md",
    "project-index.md",
    "stilguide.md",
    "tidslinje.md",
    "kontinuitetsanteckningar.md",
    "arbetslogg.md",
    "kapitel",
    "publishing/metadata.yaml",
    "publishing/epub.css",
    "publishing/fix-epub-after-pandoc.py",
    "publishing/pdf-template.tex",
    "publishing/pdf-filter.lua",
    "scripts/build_book.py",
    "scripts/validate_project.py",
)

REQUIRED_METADATA_KEYS = (
    "title",
    "author",
    "language",
)


def error(errors: list[str], message: str) -> None:
    errors.append(message)
    print(f"ERROR: {message}", file=sys.stderr)


def parse_simple_yaml_scalars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key or key.startswith("-"):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def validate_markdown_links(root: Path, errors: list[str]) -> None:
    link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for md in sorted(root.rglob("*.md")):
        if any(part in {".git"} for part in md.relative_to(root).parts):
            continue
        text = md.read_text(encoding="utf-8")
        for target in link_re.findall(text):
            target = target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if " " in target and not target.startswith(("./", "../")):
                target = target.split(" ", 1)[0]
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not target:
                continue
            candidate = (md.parent / target).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                continue
            if not candidate.exists():
                error(errors, f"Trasig intern Markdown-länk i {md.relative_to(root)}: {target}")


def strip_chapter_notes(text: str) -> str:
    # Kapitelnoteringar ligger efter första horisontella regel i projektets kapitel.
    return re.split(r"(?m)^---\s*$", text, maxsplit=1)[0].strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            error(errors, f"Obligatorisk sökväg saknas: {rel}")

    metadata_path = root / "publishing/metadata.yaml"
    if metadata_path.exists():
        metadata = parse_simple_yaml_scalars(metadata_path)
        for key in REQUIRED_METADATA_KEYS:
            if not metadata.get(key):
                error(errors, f"Metadata saknar värde för: {key}")
        if metadata.get("title") != "Nollpunkten":
            error(errors, "Metadata title måste vara 'Nollpunkten'.")
        if metadata.get("author") != "Erland Lindmark":
            error(errors, "Metadata author måste vara 'Erland Lindmark'.")

    chapter_dir = root / "kapitel"
    chapters = sorted(chapter_dir.glob("kapitel-[0-9][0-9].md")) if chapter_dir.exists() else []
    if not chapters:
        error(errors, "Inga kapitel hittades i kapitel/.")

    numbers: list[int] = []
    for chapter in chapters:
        match = CHAPTER_RE.fullmatch(chapter.name)
        if not match:
            error(errors, f"Ogiltigt kapitelfilnamn: {chapter.relative_to(root)}")
            continue
        number = int(match.group(1))
        numbers.append(number)
        text = chapter.read_text(encoding="utf-8")
        body = strip_chapter_notes(text)
        if len(body) < 500:
            error(errors, f"Kapitlet verkar tomt eller för kort: {chapter.relative_to(root)}")
        first_line = body.splitlines()[0].strip() if body.splitlines() else ""
        h1 = CHAPTER_H1_RE.match(first_line)
        if not h1:
            error(errors, f"Kapitlet saknar H1 enligt '# Kapitel X – Titel': {chapter.relative_to(root)}")
        elif int(h1.group(1)) != number:
            error(errors, f"Kapitelnummer i H1 matchar inte filnamnet: {chapter.relative_to(root)}")
        for marker in MARKERS:
            if marker in text:
                error(errors, f"Arbetsmarkör {marker!r} finns kvar i {chapter.relative_to(root)}")

    if numbers:
        expected = list(range(1, max(numbers) + 1))
        if numbers != expected:
            error(errors, f"Kapitelserien har luckor eller fel ordning: {numbers}, väntat {expected}")

    validate_markdown_links(root, errors)

    if errors:
        print(f"Validering misslyckades med {len(errors)} fel.", file=sys.stderr)
        return 1

    print(f"OK: projektet validerades ({len(chapters)} kapitel).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
