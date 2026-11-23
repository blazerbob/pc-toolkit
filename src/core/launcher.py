"""Модуль «Профили запуска»: запуск набора программ одним действием."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LaunchResult:
    item: str
    ok: bool
    error: str | None = None


def launch_item(item: str) -> LaunchResult:
    """Запускает одну программу.

    Если `item` — путь к существующему файлу, открывает его через оболочку.
    Иначе запускает как команду в командной строке.
    """
    item = item.strip()
    if not item:
        return LaunchResult(item, False, "Пустой элемент")
    try:
        if Path(item).exists():
            os.startfile(item)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(item, shell=True)
        return LaunchResult(item, True)
    except OSError as exc:
        return LaunchResult(item, False, str(exc))


def launch_profile(items: Iterable[str]) -> list[LaunchResult]:
    """Запускает все элементы профиля по очереди."""
    return [launch_item(i) for i in items]