"""Модуль очистки: временные файлы, Prefetch, корзина.

Всё построено на чистой логике (`scan_*` / `clean_target`), чтобы её можно было
тестировать на временных папках без касания реальной системы.
"""

from __future__ import annotations

import ctypes
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

# Флаги SHEmptyRecycleBinW
SHERB_NOCONFIRMATION = 0x1
SHERB_NOPROGRESSUI = 0x2
SHERB_NOSOUND = 0x4


@dataclass(frozen=True)
class CleanTarget:
    """Одна область, которую можно очистить."""

    name: str
    path: Path
    require_admin: bool = False


@dataclass
class ScanResult:
    target: CleanTarget
    files: int
    size: int
    accessible: bool


@dataclass
class CleanReport:
    name: str
    deleted: int
    freed: int
    errors: int


def default_targets() -> list[CleanTarget]:
    """Стандартный набор областей очистки для текущего пользователя."""
    dirs: list[tuple[str, str | None, bool]] = []

    tmp = os.environ.get("TEMP") or os.environ.get("TMP")
    if tmp:
        dirs.append(("Временные файлы", tmp, False))

    local = os.environ.get("LOCALAPPDATA")
    if local:
        dirs.append(("Кэш Windows", str(Path(local) / "Temp"), False))
        dirs.append(
            (
                "Кэш Internet Explorer",
                str(Path(local) / "Microsoft" / "Windows" / "INetCache"),
                False,
            )
        )

    windir = os.environ.get("WINDIR", r"C:\Windows")
    dirs.append(("Системный Temp", str(Path(windir) / "Temp"), True))
    dirs.append(("Prefetch", str(Path(windir) / "Prefetch"), True))

    seen: set[str] = set()
    out: list[CleanTarget] = []
    for name, path, admin in dirs:
        if not path:
            continue
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(CleanTarget(name, Path(path), admin))
    return out


def dir_size(path: Path) -> int:
    """Суммарный размер файлов в папке (без учёта прав/ошибок)."""
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                continue
    return total


def scan_target(target: CleanTarget) -> ScanResult:
    """Считает количество файлов и объём, который освободит очистка."""
    if not target.path.exists():
        return ScanResult(target, 0, 0, False)
    files = 0
    size = 0
    accessible = True
    try:
        for child in target.path.iterdir():
            if child.is_dir():
                files += 1
                size += dir_size(child)
            else:
                files += 1
                try:
                    size += child.stat().st_size
                except OSError:
                    pass
    except PermissionError:
        accessible = False
    return ScanResult(target, files, size, accessible)


def scan(targets: list[CleanTarget] | None = None) -> list[ScanResult]:
    return [scan_target(t) for t in (targets or default_targets())]


def clean_target(target: CleanTarget) -> CleanReport:
    """Удаляет содержимое одной области, пропуская занятые файлы."""
    if not target.path.exists():
        return CleanReport(target.name, 0, 0, 0)
    deleted = 0
    freed = 0
    errors = 0
    for child in list(target.path.iterdir()):
        try:
            if child.is_dir():
                size = dir_size(child)
                shutil.rmtree(child)
                deleted += 1
                freed += size
            else:
                size = child.stat().st_size
                child.unlink()
                deleted += 1
                freed += size
        except OSError:
            errors += 1
            continue
    return CleanReport(target.name, deleted, freed, errors)


def clean(targets: list[CleanTarget] | None = None) -> list[CleanReport]:
    return [clean_target(t) for t in (targets or default_targets())]


def empty_recycle_bin() -> bool:
    """Очищает корзину Windows. True — успех."""
    func = ctypes.windll.shell32.SHEmptyRecycleBinW
    func.restype = ctypes.c_long
    flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    try:
        return func(None, None, flags) == 0
    except OSError:
        return False


def human_size(num: float) -> str:
    """Человекочитаемый размер: 1536 -> '1.5 КБ'."""
    units = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    n = float(num)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            if unit == "Б":
                return f"{int(n)} {unit}"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} {units[-1]}"