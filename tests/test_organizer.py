from pathlib import Path

from core import organizer


def test_category_for():
    assert organizer.category_for("photo.JPG") == "Изображения"
    assert organizer.category_for("movie.mp4") == "Видео"
    assert organizer.category_for("report.pdf") == "Документы"
    assert organizer.category_for("setup.exe") == "Установщики"
    assert organizer.category_for("weird.qqq") == organizer.OTHER


def test_plan_ignores_dirs(tmp_path: Path):
    (tmp_path / "a.png").write_text("x")
    (tmp_path / "b.zip").write_text("x")
    (tmp_path / "folder").mkdir()
    plan = organizer.plan(tmp_path)
    assert len(plan) == 2
    assert {mv.category for mv in plan} == {"Изображения", "Архивы"}


def test_organize_dry_run_does_nothing(tmp_path: Path):
    (tmp_path / "a.png").write_text("x")
    report = organizer.organize(tmp_path, dry_run=True)
    assert report.moved == 1
    assert (tmp_path / "a.png").exists()


def test_organize_moves_and_handles_conflict(tmp_path: Path):
    (tmp_path / "a.png").write_text("one")
    target_dir = tmp_path / "Изображения"
    target_dir.mkdir()
    (target_dir / "a.png").write_text("existing")

    report = organizer.organize(tmp_path, dry_run=False)
    assert report.moved == 1
    assert report.errors == 0
    assert not (tmp_path / "a.png").exists()
    assert (target_dir / "a (1).png").exists()