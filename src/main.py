"""Точка входа PC Toolkit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    try:
        from ui.app import PCToolkitApp
    except ImportError as exc:  # pragma: no cover - зависит от окружения
        print(f"Не удалось загрузить GUI: {exc}")
        print("Проверь, что tkinter доступен в этой сборке Python.")
        return 1

    app = PCToolkitApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())