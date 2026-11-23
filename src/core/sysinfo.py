"""Модуль «Инфо о системе»: диски, память, аптайм."""

from __future__ import annotations

import ctypes
import shutil
import string
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class DiskInfo:
    mount: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class MemoryInfo:
    total: int
    available: int
    percent: float


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def logical_drives() -> list[str]:
    """Буквы дисков, которые сейчас доступны."""
    try:
        mask = ctypes.windll.kernel32.GetLogicalDrives()
    except OSError:
        return []
    drives: list[str] = []
    for i, letter in enumerate(string.ascii_uppercase):
        if mask & (1 << i):
            drives.append(f"{letter}:\\")
    return drives


def disks() -> list[DiskInfo]:
    out: list[DiskInfo] = []
    for mount in logical_drives():
        try:
            usage = shutil.disk_usage(mount)
        except OSError:
            continue
        percent = (usage.used / usage.total * 100) if usage.total else 0.0
        out.append(DiskInfo(mount, usage.total, usage.used, usage.free, percent))
    return out


def memory() -> MemoryInfo | None:
    """Информация о физической памяти через WinAPI."""
    stat = _MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    try:
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    except OSError:
        return None
    if not ok:
        return None
    return MemoryInfo(
        total=int(stat.ullTotalPhys),
        available=int(stat.ullAvailPhys),
        percent=float(stat.dwMemoryLoad),
    )


def uptime() -> timedelta:
    """Время с момента загрузки системы."""
    try:
        func = ctypes.windll.kernel32.GetTickCount64
        func.restype = ctypes.c_ulonglong
        millis = int(func())
    except OSError:
        return timedelta(0)
    return timedelta(milliseconds=millis)


def human_size(num: float) -> str:
    units = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    n = float(num)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            if unit == "Б":
                return f"{int(n)} {unit}"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} {units[-1]}"


def human_uptime(td: timedelta) -> str:
    total = int(td.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} д")
    parts.append(f"{hours} ч")
    parts.append(f"{minutes} мин")
    return " ".join(parts)