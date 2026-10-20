import csv
from pathlib import Path

from PIL import Image

from scripts.catalog.validate_csv import REQUIRED, main


def _create_jpeg(path: Path, size: tuple[int, int] = (1200, 1200), color: tuple[int, int, int] = (200, 100, 100)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(path, format="JPEG")


def _write_csv(path: Path, rows: list[dict[str, str]], columns: list[str] | None = None) -> None:
    cols = columns if columns is not None else REQUIRED
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _base_row(item_id: str = "g001", image_rel: str = "images/g001.jpg") -> dict[str, str]:
    return {
        "id": item_id,
        "title": "Classic Cotton Tee",
        "brand": "Own",
        "price": "1499",
        "gender": "unisex",
        "category": "top",
        "sub_category": "tshirt",
        "primary_color": "blue",
        "pattern": "solid",
        "formality": "2",
        "ethnic_wear": "false",
        "tryon_suitable": "true",
        "sizes": "S|M|L",
        "image": image_rel,
    }


def test_valid_csv_passes(tmp_path: Path, capsys) -> None:
    img_path = tmp_path / "images" / "g001.jpg"
    _create_jpeg(img_path, size=(1200, 1200), color=(10, 20, 30))

    csv_path = tmp_path / "catalog.csv"
    _write_csv(csv_path, [_base_row("g001", "images/g001.jpg")])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 0
    assert "OK" in out
    assert "0 error(s)" not in out  # printed "OK" directly


def test_missing_column_returns_error(tmp_path: Path, capsys) -> None:
    cols = [c for c in REQUIRED if c != "category"]
    csv_path = tmp_path / "catalog.csv"
    _write_csv(csv_path, [_base_row()], columns=cols)

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "missing columns: ['category']" in out


def test_empty_csv_returns_error(tmp_path: Path, capsys) -> None:
    csv_path = tmp_path / "catalog.csv"
    csv_path.write_text("", encoding="utf-8-sig")

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "empty csv" in out


def test_bad_gender_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["gender"] = "alien"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "gender must be one of" in out


def test_bad_category_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["category"] = "footwear"  # not in CATEGORIES
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "category must be one of" in out


def test_bad_color_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["primary_color"] = "neon_chartreuse"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "primary_color must be one of" in out


def test_bad_pattern_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["pattern"] = "polka_dot"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "pattern must be one of" in out


def test_formality_out_of_range_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["formality"] = "6"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "formality must be 1-5" in out


def test_non_numeric_price_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["price"] = "twelve_hundred"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "price not a number" in out


def test_negative_price_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["price"] = "-500"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "price must be positive" in out


def test_empty_and_unknown_sizes_fail(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")
    csv_path = tmp_path / "catalog.csv"

    # 1. Empty sizes
    row1 = _base_row()
    row1["sizes"] = ""
    _write_csv(csv_path, [row1])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()
    assert code == 1
    assert "sizes must be a '|'-separated subset of" in out

    # 2. Unknown size
    row2 = _base_row()
    row2["sizes"] = "S|UNKNOWN_SIZE"
    _write_csv(csv_path, [row2])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()
    assert code == 1
    assert "sizes must be a '|'-separated subset of" in out


def test_missing_image_file_fails(tmp_path: Path, capsys) -> None:
    csv_path = tmp_path / "catalog.csv"
    _write_csv(csv_path, [_base_row("g001", "images/non_existent.jpg")])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "image not found: images/non_existent.jpg" in out


def test_duplicate_id_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg", color=(10, 20, 30))
    _create_jpeg(tmp_path / "images" / "g002.jpg", color=(40, 50, 60))

    csv_path = tmp_path / "catalog.csv"
    row1 = _base_row("g001", "images/g001.jpg")
    row2 = _base_row("g001", "images/g002.jpg")  # duplicate id
    _write_csv(csv_path, [row1, row2])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "duplicate id" in out


def test_duplicate_image_content_fails(tmp_path: Path, capsys) -> None:
    # Same exact pixels -> identical sha256
    _create_jpeg(tmp_path / "images" / "g001.jpg", color=(100, 150, 200))
    _create_jpeg(tmp_path / "images" / "g002.jpg", color=(100, 150, 200))

    csv_path = tmp_path / "catalog.csv"
    row1 = _base_row("g001", "images/g001.jpg")
    row2 = _base_row("g002", "images/g002.jpg")
    _write_csv(csv_path, [row1, row2])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "same image as g001" in out


def test_tryon_suitable_true_with_outerwear_fails(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")

    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["category"] = "outerwear"
    row["tryon_suitable"] = "true"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 1
    assert "tryon_suitable=true needs a try-on supported category (top, bottom, one_piece)" in out


def test_tryon_suitable_false_with_outerwear_passes(tmp_path: Path, capsys) -> None:
    _create_jpeg(tmp_path / "images" / "g001.jpg")

    csv_path = tmp_path / "catalog.csv"
    row = _base_row()
    row["category"] = "outerwear"
    row["tryon_suitable"] = "false"
    _write_csv(csv_path, [row])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 0
    assert "OK" in out


def test_small_image_gives_warning_not_error(tmp_path: Path, capsys) -> None:
    # 500x500 is < 1000 px, so should warn but still return 0 (OK)
    _create_jpeg(tmp_path / "images" / "g001.jpg", size=(500, 500))

    csv_path = tmp_path / "catalog.csv"
    _write_csv(csv_path, [_base_row("g001", "images/g001.jpg")])

    code = main(str(csv_path))
    out, _ = capsys.readouterr()

    assert code == 0
    assert "WARN " in out
    assert "at least 1000 px on the short side is better" in out
    assert "OK" in out
