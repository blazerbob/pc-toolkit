"""Хранение настроек PC Toolkit в JSON.

Настройки лежат в `%APPDATA%/PCToolkit/config.json` (либо рядом с проектом,
если APPDATA недоступен). Файл создаётся лениво.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "downloads_dir": "",
    "backup_dest": "",
    "backup_sources": [],
    "profiles": {
        "Работа": [],
        "Игры": [],
        "Учёба": [],
    },
}


def config_dir() -> Path:
    """Папка для конфига."""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    return root / "PCToolkit"


def config_path() -> Path:
    return config_dir() / "config.json"


def load() -> dict[str, Any]:
    """Читает конфиг, дополняя недостающие ключи значениями по умолчанию."""
    data = dict(DEFAULTS)
    path = config_path()
    if path.exists():
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                data.update(stored)
        except (OSError, json.JSONDecodeError):
            pass
    return data


def save(data: dict[str, Any]) -> Path:
    """Сохраняет конфиг, создавая папку при необходимости."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def update(**changes: Any) -> dict[str, Any]:
    """Обновляет отдельные ключи и сохраняет."""
    data = load()
    data.update(changes)
    save(data)
    return data