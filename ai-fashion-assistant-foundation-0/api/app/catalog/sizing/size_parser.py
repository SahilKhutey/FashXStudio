import re
from dataclasses import dataclass


@dataclass
class ParsedSizeRow:
    size_label: str
    chest_cm: float | None = None
    length_cm: float | None = None
    waist_cm: float | None = None
    shoulder_cm: float | None = None
    confidence: float = 0.90
    needs_review: bool = False


class SizeChartParser:
    """Parses retailer size chart tables into normalized centimeter measurements."""

    INCH_TO_CM = 2.54

    @classmethod
    def _parse_value(cls, raw: str | float | int | None, unit: str = "cm") -> float | None:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            val = float(raw)
            return (
                round(val * cls.INCH_TO_CM, 1)
                if unit.lower() in ("in", "inch", "inches")
                else round(val, 1)
            )

        val_str = str(raw).strip().lower()
        if not val_str:
            return None

        # Check for range: e.g. "38-40" or "38 - 40"
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)", val_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            mid = (low + high) / 2.0
            is_inches = unit.lower() in ("in", "inch", "inches") or "in" in val_str
            return round(mid * cls.INCH_TO_CM, 1) if is_inches else round(mid, 1)

        num_match = re.search(r"(\d+(?:\.\d+)?)", val_str)
        if num_match:
            val = float(num_match.group(1))
            is_inches = unit.lower() in ("in", "inch", "inches") or "in" in val_str
            return round(val * cls.INCH_TO_CM, 1) if is_inches else round(val, 1)

        return None

    @classmethod
    def parse_table(
        cls,
        rows: list[dict[str, str | float | int]],
        default_unit: str = "cm",
    ) -> list[ParsedSizeRow]:
        """Parse raw size rows into structured ParsedSizeRow records with physical plausibility validation."""
        results: list[ParsedSizeRow] = []

        for row in rows:
            size_label = str(row.get("size") or row.get("size_label") or "").strip().upper()
            if not size_label:
                continue

            unit = str(row.get("unit") or default_unit)
            chest = cls._parse_value(row.get("chest"), unit)
            length = cls._parse_value(row.get("length"), unit)
            waist = cls._parse_value(row.get("waist"), unit)
            shoulder = cls._parse_value(row.get("shoulder"), unit)

            confidence = 0.95
            needs_review = False

            # Plausibility checks for human garments
            if chest is not None and (chest < 60.0 or chest > 170.0):
                confidence = 0.50
                needs_review = True
            if waist is not None and (waist < 40.0 or waist > 160.0):
                confidence = 0.50
                needs_review = True
            if length is not None and (length < 30.0 or length > 160.0):
                confidence = 0.50
                needs_review = True

            results.append(
                ParsedSizeRow(
                    size_label=size_label,
                    chest_cm=chest,
                    length_cm=length,
                    waist_cm=waist,
                    shoulder_cm=shoulder,
                    confidence=confidence,
                    needs_review=needs_review,
                )
            )

        return results
