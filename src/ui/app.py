"""GUI PC Toolkit на Tkinter (только стандартная библиотека)."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import TypeVar

from core import backup, cleaner, config, launcher, organizer, power, sysinfo

PAD = 8


T = TypeVar("T")


def run_async_generic(
    widget: tk.Misc,
    func: Callable[[], T],
    on_done: Callable[[T], None],
) -> None:
    """Выполняет `func` в потоке, результат отдаёт в UI через `on_done`."""
    result_queue: queue.Queue[object] = queue.Queue()

    def worker() -> None:
        try:
            result_queue.put(func())
        except Exception as exc:  # noqa: BLE001 - показываем любую ошибку в UI
            result_queue.put(f"Ошибка: {exc}")

    threading.Thread(target=worker, daemon=True).start()

    def poll() -> None:
        try:
            on_done(result_queue.get_nowait())  # type: ignore[arg-type]
        except queue.Empty:
            widget.after(80, poll)

    widget.after(80, poll)


def run_async(
    widget: tk.Misc,
    func: Callable[[], str],
    on_done: Callable[[str], None],
) -> None:
    run_async_generic(widget, func, on_done)


class PCToolkitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PC Toolkit — автоматизатор ПК")
        self.geometry("760x560")
        self.minsize(680, 480)
        self.cfg = config.load()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        self._build_clean_tab(notebook)
        self._build_organizer_tab(notebook)
        self._build_backup_tab(notebook)
        self._build_launcher_tab(notebook)
        self._build_power_tab(notebook)
        self._build_info_tab(notebook)

        self.status = tk.StringVar(value="Готов")
        ttk.Label(self, textvariable=self.status, anchor="w", relief="sunken").pack(
            fill="x", side="bottom"
        )

    # ---------- Очистка ----------
    def _build_clean_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="🧹 Очистка")

        self.clean_list = tk.Listbox(frame, selectmode="extended", height=8)
        self.clean_list.pack(fill="both", expand=True)
        self.clean_results: list[cleaner.ScanResult] = []

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=(PAD, 0))
        ttk.Button(btns, text="Сканировать", command=self._clean_scan).pack(side="left")
        ttk.Button(btns, text="Очистить выбранное", command=self._clean_run).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(btns, text="Очистить корзину", command=self._empty_bin).pack(
            side="left", padx=(4, 0)
        )

    def _clean_scan(self) -> None:
        self.status.set("Сканирую временные файлы…")

        def job() -> list[cleaner.ScanResult]:
            return cleaner.scan()

        def done(results: list[cleaner.ScanResult]) -> None:
            self.clean_results = results
            self.clean_list.delete(0, tk.END)
            for r in results:
                mark = "" if r.accessible else " ⚠ (нужны права)"
                self.clean_list.insert(
                    "end",
                    f"{r.target.name:<26} — {cleaner.human_size(r.size)} ({r.files} объ.){mark}",
                )
            self.status.set("Сканирование завершено")

        run_async_generic(self, job, done)

    def _clean_run(self) -> None:
        indexes = self.clean_list.curselection()
        if not indexes:
            messagebox.showinfo("Очистка", "Выбери хотя бы одну область.")
            return
        targets = [self.clean_results[i].target for i in indexes]
        self.status.set("Очищаю…")

        def job() -> str:
            reports = cleaner.clean(targets)
            total = sum(r.freed for r in reports)
            return f"Освобождено: {cleaner.human_size(total)}"

        run_async(self, job, lambda t: (self.status.set(t), self._clean_scan()))

    def _empty_bin(self) -> None:
        if messagebox.askyesno("Корзина", "Очистить корзину без возможности восстановления?"):
            ok = cleaner.empty_recycle_bin()
            self.status.set("Корзина очищена" if ok else "Не удалось очистить корзину")

    # ---------- Организатор ----------
    def _build_organizer_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="📁 Загрузки")

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text="Папка:").pack(side="left")
        self.org_path = tk.StringVar(value=self.cfg.get("downloads_dir") or "")
        ttk.Entry(row, textvariable=self.org_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="…", width=3, command=lambda: self._pick_dir(self.org_path)).pack(
            side="left"
        )

        self.org_dry = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, text="Только предпросмотр (не перемещать)", variable=self.org_dry
        ).pack(anchor="w", pady=4)

        ttk.Button(frame, text="Организовать", command=self._organize).pack(anchor="w")
        self.org_log = ScrolledText(frame, height=10, state="disabled")
        self.org_log.pack(fill="both", expand=True, pady=(PAD, 0))

    def _organize(self) -> None:
        folder = Path(self.org_path.get())
        dry = self.org_dry.get()
        self._log(self.org_log, f"Папка: {folder}  (предпросмотр={dry})")

        def job() -> str:
            plan = organizer.plan(folder)
            lines = [f"{mv.src.name}  →  {mv.category}" for mv in plan]
            if not dry:
                report = organizer.organize(folder, dry_run=False)
                lines.append(f"\nПеремещено: {report.moved}, ошибок: {report.errors}")
                config.save({**self.cfg, "downloads_dir": str(folder)})
            else:
                lines.append(f"\nФайлов к раскладке: {len(plan)}")
            return "\n".join(lines)

        run_async(self, job, lambda t: (self._log(self.org_log, t), self.status.set("Готово")))

    # ---------- Бэкап ----------
    def _build_backup_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="💾 Бэкап")

        ttk.Label(frame, text="Что копировать:").pack(anchor="w")
        self.backup_list = tk.Listbox(frame, height=6)
        self.backup_list.pack(fill="both", expand=True)
        for src in self.cfg.get("backup_sources", []):
            self.backup_list.insert("end", src)

        b = ttk.Frame(frame)
        b.pack(fill="x", pady=4)
        ttk.Button(b, text="Добавить папку", command=self._backup_add).pack(side="left")
        ttk.Button(b, text="Убрать", command=self._backup_remove).pack(side="left", padx=4)

        row = ttk.Frame(frame)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Куда:").pack(side="left")
        self.backup_dest = tk.StringVar(value=self.cfg.get("backup_dest") or "")
        ttk.Entry(row, textvariable=self.backup_dest).pack(
            side="left", fill="x", expand=True, padx=4
        )
        ttk.Button(row, text="…", width=3, command=lambda: self._pick_dir(self.backup_dest)).pack(
            side="left"
        )

        ttk.Button(frame, text="Сделать бэкап", command=self._backup_run).pack(anchor="w")
        self.backup_log = ScrolledText(frame, height=8, state="disabled")
        self.backup_log.pack(fill="both", expand=True, pady=(PAD, 0))

    def _backup_add(self) -> None:
        path = filedialog.askdirectory(title="Папка для бэкапа")
        if path:
            self.backup_list.insert("end", path)

    def _backup_remove(self) -> None:
        for i in reversed(self.backup_list.curselection()):
            self.backup_list.delete(i)

    def _backup_run(self) -> None:
        sources = [Path(self.backup_list.get(i)) for i in range(self.backup_list.size())]
        dest = Path(self.backup_dest.get())
        if not sources or not str(dest):
            messagebox.showinfo("Бэкап", "Укажи источники и папку назначения.")
            return
        self.status.set("Копирую…")

        def job() -> str:
            report = backup.create_backup(sources, dest)
            config.save(
                {
                    **self.cfg,
                    "backup_sources": [str(s) for s in sources],
                    "backup_dest": str(dest),
                }
            )
            errs = "\n".join(report.errors) if report.errors else "без ошибок"
            return (
                f"Готово: {report.dest}\n"
                f"Файлов: {report.copied_files}, "
                f"объём: {cleaner.human_size(report.copied_bytes)}\n{errs}"
            )

        run_async(self, job, lambda t: (self._log(self.backup_log, t), self.status.set("Готово")))

    # ---------- Профили запуска ----------
    def _build_launcher_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="🚀 Профили")

        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text="Профиль:").pack(side="left")
        self.profile_name = tk.StringVar(value="Работа")
        self.profile_combo = ttk.Combobox(
            row, textvariable=self.profile_name, values=list(self.cfg["profiles"]), state="readonly"
        )
        self.profile_combo.pack(side="left", padx=4)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self._load_profile())
        ttk.Button(row, text="Новый", command=self._new_profile).pack(side="left")

        self.profile_list = tk.Listbox(frame, height=8)
        self.profile_list.pack(fill="both", expand=True, pady=4)

        b = ttk.Frame(frame)
        b.pack(fill="x")
        ttk.Button(b, text="Добавить программу", command=self._profile_add).pack(side="left")
        ttk.Button(b, text="Убрать", command=self._profile_remove).pack(side="left", padx=4)
        ttk.Button(b, text="Сохранить", command=self._save_profile).pack(side="left", padx=4)
        ttk.Button(b, text="▶ Запустить", command=self._run_profile).pack(side="right")

        self._load_profile()

    def _current_profile_items(self) -> list[str]:
        return [self.profile_list.get(i) for i in range(self.profile_list.size())]

    def _load_profile(self) -> None:
        self.profile_list.delete(0, tk.END)
        for item in self.cfg["profiles"].get(self.profile_name.get(), []):
            self.profile_list.insert("end", item)

    def _new_profile(self) -> None:
        name = simpledialog_name(self)
        if not name:
            return
        self.cfg["profiles"].setdefault(name, [])
        config.save(self.cfg)
        self.profile_combo["values"] = list(self.cfg["profiles"])
        self.profile_name.set(name)
        self._load_profile()

    def _profile_add(self) -> None:
        path = filedialog.askopenfilename(title="Программа или файл")
        if path:
            self.profile_list.insert("end", path)

    def _profile_remove(self) -> None:
        for i in reversed(self.profile_list.curselection()):
            self.profile_list.delete(i)

    def _save_profile(self) -> None:
        self.cfg["profiles"][self.profile_name.get()] = self._current_profile_items()
        config.save(self.cfg)
        self.status.set(f"Профиль «{self.profile_name.get()}» сохранён")

    def _run_profile(self) -> None:
        items = self._current_profile_items()
        if not items:
            messagebox.showinfo("Профили", "Профиль пуст.")
            return

        def job() -> str:
            results = launcher.launch_profile(items)
            ok = sum(r.ok for r in results)
            bad = [f"{r.item}: {r.error}" for r in results if not r.ok]
            return f"Запущено: {ok}/{len(results)}" + ("\n" + "\n".join(bad) if bad else "")

        run_async(self, job, lambda t: messagebox.showinfo("Профили", t))

    # ---------- Таймер питания ----------
    def _build_power_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="⏻ Питание")

        row = ttk.Frame(frame)
        row.pack(anchor="w", pady=4)
        ttk.Label(row, text="Через (минут):").pack(side="left")
        self.power_minutes = tk.IntVar(value=30)
        ttk.Spinbox(row, from_=0, to=1440, textvariable=self.power_minutes, width=6).pack(
            side="left", padx=4
        )

        grid = ttk.Frame(frame)
        grid.pack(anchor="w", pady=PAD)
        buttons = [
            ("Выключить", lambda: self._power("s"), 0, 0),
            ("Перезагрузить", lambda: self._power("r"), 0, 1),
            ("Сон", lambda: self._power("sleep"), 0, 2),
            ("Гибернация", lambda: self._power("h"), 1, 0),
            ("Отменить", self._power_cancel, 1, 1),
        ]
        for text, cmd, r, c in buttons:
            ttk.Button(grid, text=text, command=cmd).grid(row=r, column=c, padx=4, pady=4)

    def _power(self, kind: str) -> None:
        minutes = int(self.power_minutes.get())
        seconds = minutes * 60
        if kind in ("s", "r") and minutes > 0:
            if not messagebox.askyesno(
                "Питание", f"{'Выключить' if kind == 's' else 'Перезагрузить'} через {minutes} мин?"
            ):
                return
        if kind == "s":
            ok = power.shutdown(seconds)
        elif kind == "r":
            ok = power.restart(seconds)
        elif kind == "sleep":
            ok = power.sleep()
        else:
            ok = power.hibernate()
        self.status.set("Команда отправлена" if ok else "Команда не выполнена")

    def _power_cancel(self) -> None:
        self.status.set("Отменено" if power.cancel() else "Нечего отменять")

    # ---------- Инфо о системе ----------
    def _build_info_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb, padding=PAD)
        nb.add(frame, text="📊 Система")
        ttk.Button(frame, text="Обновить", command=self._refresh_info).pack(anchor="w")
        self.info_text = ScrolledText(frame, state="disabled")
        self.info_text.pack(fill="both", expand=True, pady=(PAD, 0))
        self._refresh_info()

    def _refresh_info(self) -> None:
        def job() -> str:
            lines = ["Диски:"]
            for d in sysinfo.disks():
                lines.append(
                    f"  {d.mount}  {sysinfo.human_size(d.used)} / "
                    f"{sysinfo.human_size(d.total)}  ({d.percent:.0f}%)"
                )
            mem = sysinfo.memory()
            if mem:
                lines.append(
                    f"\nПамять: {sysinfo.human_size(mem.total - mem.available)} / "
                    f"{sysinfo.human_size(mem.total)}  ({mem.percent:.0f}%)"
                )
            lines.append(f"\nАптайм: {sysinfo.human_uptime(sysinfo.uptime())}")
            return "\n".join(lines)

        run_async(self, job, lambda t: self._set_text(self.info_text, t))

    # ---------- Утилиты ----------
    def _pick_dir(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    @staticmethod
    def _set_text(widget: ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _log(self, widget: ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.insert(tk.END, text + "\n")
        widget.see(tk.END)
        widget.configure(state="disabled")


def simpledialog_name(parent: tk.Misc) -> str | None:
    from tkinter import simpledialog

    return simpledialog.askstring("Новый профиль", "Название профиля:", parent=parent)