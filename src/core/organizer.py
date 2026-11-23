"""Модуль «Организатор Загрузок»: раскладка файлов по категориям.

Категория определяется по расширению. Логика — чистые функции, легко тестируются.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

OTHER = "Прочее"

CATEGORIES: dict[str, set[str]] = {
    "Изображения": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp",
        ".webp", ".tiff", ".svg", ".ico", ".heic",
    },
    "Видео": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg"},
    "Аудио": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"},
    "Документы": {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".rtf", ".odt", ".csv", ".md",
    },
    "Архивы": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".cab"},
    "Установщики": {".exe", ".msi", ".msix", ".appx", ".bat", ".cmd", ".ps1"},
    "Код": {
        ".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
        ".c", ".cpp", ".cs", ".java", ".go", ".rs", ".sh",
    },
}

_EXT_TO_CATEGORY: dict[str, str] = {
    ext: cat for cat, exts in CATEGORIES.items() for ext in exts
}


@dataclass(frozen=True)
class Move:
    src: Path
    dest: Path
    category: str


@dataclass
class OrganizeReport:
    moved: int
    skipped: int
    errors: int
    dest_root: Path


def category_for(filename: str) -> str:
    """Категория по имени/расширению файла."""
    ext = Path(filename).suffix.lower()
    return _EXT_TO_CATEGORY.get(ext, OTHER)


def known_extensions() -> set[str]:
    return set(_EXT_TO_CATEGORY)


def plan(folder: Path) -> list[Move]:
    """Строит план перемещений для файлов верхнего уровня папки.

    Папки и уже отсортированные подкатегории игнорируются.
    """
    moves: list[Move] = []
    if not folder.exists():
        return moves
    for child in sorted(folder.iterdir()):
        if not child.is_file():
            continue
        if child.name.startswith("."):
            continue
        cat = category_for(child.name)
        moves.append(Move(child, folder / cat / child.name, cat))
    return moves


def organize(folder: Path, dry_run: bool = False) -> OrganizeReport:
    """Раскладывает файлы по категориям.

    `dry_run=True` — только считает, ничего не трогает.
    Конфликты имён решаются добавлением ` (1)`, ` (2)` и т.д.
    """
    moves = plan(folder)
    moved = skipped = errors = 0
    for mv in moves:
        if dry_run:
            moved += 1
            continue
        try:
            mv.dest.parent.mkdir(parents=True, exist_ok=True)
            final = _unique_path(mv.dest)
            mv.src.replace(final)
            moved += 1
        except OSError:
            errors += 1
    return OrganizeReport(moved, skipped, errors, folder)


def _unique_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1