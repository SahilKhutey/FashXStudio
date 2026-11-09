"""RC11 Pilot data export validator and privacy quarantine verifier."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FORBIDDEN_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),  # email
    re.compile(r"(?:\+91|0)?[6-9]\d{9}"),  # phone number
    re.compile(r"https?://[^\s]+\?(?:AWSAccessKeyId|Signature|X-Amz-Signature)="),  # signed URLs
    re.compile(r"data:image/[a-zA-Z]+;base64,"),  # embedded base64 image bytes
]

FORBIDDEN_KEYS = {
    "email",
    "phone",
    "name",
    "full_name",
    "image_bytes",
    "image_url",
    "signed_url",
    "waist_cm",
    "chest_cm",
    "hip_cm",
    "height_cm",
    "weight_kg",
    "skin_tone",
    "raw_photo",
}


def scan_for_pii(data: Any, path: str = "") -> list[str]:
    """Recursively checks that no forbidden PII, measurements, or raw image payloads exist."""
    errors: list[str] = []

    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k
            if k.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{current_path}")
            errors.extend(scan_for_pii(v, current_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            errors.extend(scan_for_pii(item, f"{path}[{idx}]"))
    elif isinstance(data, str):
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(data):
                errors.append(f"pii_pattern_match:{path}")
                break

    return errors


def validate_export_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validates the export manifest metadata."""
    errors: list[str] = []
    required = (
        "pilot_id",
        "period_start",
        "period_end",
        "extracted_at",
        "evidence_type",
        "source_reference",
    )
    for field in required:
        if not manifest.get(field):
            errors.append(f"missing_manifest_field:{field}")

    if manifest.get("evidence_type") != "real":
        errors.append("evidence_type_not_real")

    for dt_field in ("period_start", "period_end", "extracted_at"):
        val = manifest.get(dt_field)
        if val:
            try:
                datetime.fromisoformat(str(val))
            except Exception:
                errors.append(f"invalid_iso_timestamp:{dt_field}")

    return errors


def validate_pilot_export(file_path: Path) -> tuple[bool, list[str]]:
    """Validates a pilot snapshot file for schema completeness, PII quarantine, and manifest rules."""
    if not file_path.exists():
        return False, [f"file_not_found:{file_path}"]

    try:
        content = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"invalid_json:{exc}"]

    errors: list[str] = []

    # 1. PII Scan
    pii_violations = scan_for_pii(content)
    errors.extend(pii_violations)

    # 2. Manifest & Metadata validation
    meta = content.get("metadata", {})
    manifest_errors = validate_export_manifest(meta)
    errors.extend(manifest_errors)

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Pilot Data Export")
    parser.add_argument("--input", type=Path, required=True, help="Path to pilot_snapshot.json")
    args = parser.parse_args()

    passed, errors = validate_pilot_export(args.input)
    if passed:
        print("PILOT DATA VALIDATION: PASS (Zero PII, valid metadata, real evidence type)")
    else:
        print(f"PILOT DATA VALIDATION: FAILED ({len(errors)} errors)")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
