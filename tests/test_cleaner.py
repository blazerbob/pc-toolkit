from pathlib import Path

from core import cleaner


def test_human_size():
    assert cleaner.human_size(512) == "512 Б"
    assert cleaner.human_size(1536) == "1.5 КБ"
    assert cleaner.human_size(1024 * 1024) == "1.0 МБ"


def test_scan_and_clean(tmp_path: Path):
    (tmp_path / "a.txt").write_bytes(b"x" * 100)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"y" * 900)

    target = cleaner.CleanTarget("Тест", tmp_path)
    result = cleaner.scan_target(target)
    assert result.accessible
    assert result.size == 1000
    assert result.files == 2

    report = cleaner.clean_target(target)
    assert report.freed == 1000
    assert report.errors == 0
    assert list(tmp_path.iterdir()) == []


def test_scan_missing_dir(tmp_path: Path):
    target = cleaner.CleanTarget("Нет", tmp_path / "nope")
    result = cleaner.scan_target(target)
    assert result.accessible is False
    assert result.size == 0