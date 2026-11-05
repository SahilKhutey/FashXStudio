from pathlib import Path

from audit.rc00.inventory import scan_repository


def test_inventory_detects_python_files(tmp_path: Path):
    source = tmp_path / "backend" / "fashx"
    source.mkdir(parents=True)
    (source / "main.py").write_text("app = None", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["file_count"] == 1
    assert result["extension_counts"][".py"] == 1


def test_inventory_excludes_env_files(tmp_path: Path):
    (tmp_path / ".env").write_text("SECRET=do-not-read", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["file_count"] == 0


def test_inventory_excludes_node_modules(tmp_path: Path):
    directory = tmp_path / "mobile" / "node_modules"
    directory.mkdir(parents=True)
    (directory / "package.json").write_text("{}", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["file_count"] == 0
