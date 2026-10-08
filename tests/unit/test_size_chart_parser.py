from fashx.catalog.sizing.size_parser import SizeChartParser


def test_size_chart_parser_parses_centimeter_table() -> None:
    raw_rows = [
        {"size": "S", "chest": 96, "waist": 82, "length": 72, "shoulder": 44, "unit": "cm"},
        {"size": "M", "chest": 102, "waist": 88, "length": 74, "shoulder": 46, "unit": "cm"},
        {"size": "L", "chest": 108, "waist": 94, "length": 76, "shoulder": 48, "unit": "cm"},
    ]
    parsed = SizeChartParser.parse_table(raw_rows, default_unit="cm")
    assert len(parsed) == 3
    assert parsed[1].size_label == "M"
    assert parsed[1].chest_cm == 102.0
    assert parsed[1].waist_cm == 88.0
    assert parsed[1].length_cm == 74.0
    assert parsed[1].shoulder_cm == 46.0
    assert parsed[1].confidence >= 0.90
    assert parsed[1].needs_review is False


def test_size_chart_parser_converts_inches_and_ranges() -> None:
    raw_rows = [
        {"size": "38", "chest": "38-40", "length": "29", "unit": "inches"},
        {"size": "40", "chest": "40-42", "length": "30", "unit": "inches"},
    ]
    parsed = SizeChartParser.parse_table(raw_rows, default_unit="in")
    assert len(parsed) == 2
    # Midpoint of 38-40 is 39 inches * 2.54 = 99.06 -> 99.1 cm
    assert parsed[0].chest_cm == 99.1
    # 29 inches * 2.54 = 73.66 -> 73.7 cm
    assert parsed[0].length_cm == 73.7


def test_size_chart_parser_flags_anomalous_measurements() -> None:
    raw_rows = [
        {"size": "XL", "chest": "250", "unit": "cm"},  # Plausibility violation
    ]
    parsed = SizeChartParser.parse_table(raw_rows)
    assert len(parsed) == 1
    assert parsed[0].needs_review is True
    assert parsed[0].confidence == 0.50
