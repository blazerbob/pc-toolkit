"""Модуль бэкапа: копирование выбранных папок с меткой даты."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class BackupReport:
    dest: Path
    copied_files: int = 0
    copied_bytes: int = 0
    errors: list[str] = field(default_factory=list)


def _dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def create_backup(
    sources: list[Path],
    dest_root: Path,
    name: str | None = None,
) -> BackupReport:
    """Копирует каждый источник в `dest_root/<name>_<timestamp>/`.

    Каждая папка-источник кладётся как отдельная подпапка с её именем.
    Файлы-источники копируются напрямую. Ошибки собираются в отчёте, не падают.
    """
    stamp = f"{name}_{timestamp()}" if name else timestamp()
    dest = dest_root / stamp
    report = BackupReport(dest=dest)
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        report.errors.append(f"Не удалось создать {dest}: {exc}")
        return report

    for src in sources:
        src = Path(src)
        if not src.exists():
            report.errors.append(f"Нет источника: {src}")
            continue
        try:
            if src.is_dir():
                target = dest / src.name
                shutil.copytree(src, target, dirs_exist_ok=True)
                report.copied_files += _count_files(target)
                report.copied_bytes += _dir_size(target)
            else:
                target = dest / src.name
                shutil.copy2(src, target)
                report.copied_files += 1
                report.copied_bytes += target.stat().st_size
        except OSError as exc:
            report.errors.append(f"{src}: {exc}")
    return report


def _count_files(path: Path) -> int:
    return sum(len(files) for _root, _dirs, files in os.walk(path))