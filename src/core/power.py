"""Модуль таймера питания: выключение, перезагрузка, сон, отмена.

Обёртки над `shutdown.exe` и `rundll32`. Каждая функция возвращает True при успехе.
"""

from __future__ import annotations

import subprocess


def _run(args: list[str]) -> bool:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def shutdown(delay_seconds: int = 0, force: bool = True) -> bool:
    args = ["shutdown", "/s", "/t", str(max(0, delay_seconds))]
    if force:
        args.append("/f")
    return _run(args)


def restart(delay_seconds: int = 0, force: bool = True) -> bool:
    args = ["shutdown", "/r", "/t", str(max(0, delay_seconds))]
    if force:
        args.append("/f")
    return _run(args)


def sleep() -> bool:
    """Усыпляет ПК (если сон доступен; иначе может уйти в гибернацию)."""
    return _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])


def hibernate() -> bool:
    return _run(["shutdown", "/h"])


def cancel() -> bool:
    """Отменяет запланированное выключение/перезагрузку."""
    return _run(["shutdown", "/a"])