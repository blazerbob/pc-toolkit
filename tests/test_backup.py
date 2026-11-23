from pathlib import Path

from core import backup


def test_create_backup_copies_tree(tmp_path: Path):
    src = tmp_path / "docs"
    src.mkdir()
    (src / "a.txt").write_text("hello")
    (src / "sub").mkdir()
    (src / "sub" / "b.txt").write_text("world")

    dest_root = tmp_path / "backups"
    report = backup.create_backup([src], dest_root, name="test")

    assert report.errors == []
    assert report.copied_files == 2
    assert (report.dest / "docs" / "sub" / "b.txt").read_text() == "world"


def test_create_backup_missing_source(tmp_path: Path):
    report = backup.create_backup([tmp_path / "ghost"], tmp_path / "out")
    assert report.errors
    assert report.copied_files == 0