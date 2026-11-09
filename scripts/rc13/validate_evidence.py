"""RC13 Evidence validator and quarantine verifier."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ALLOWED_STATUS: frozenset[str] = frozenset({"pass", "fail", "unknown", "in_progress"})
ALLOWED_TYPES: frozenset[str] = frozenset(
    {"technical", "product", "market", "vto", "catalog", "compliance", "security"}
)

FORBIDDEN_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),  # email
    re.compile(r"(?:\+91|0)?[6-9]\d{9}"),  # phone number
    re.compile(r"https?://[^\s]+\?(?:AWSAccessKeyId|Signature|X-Amz-Signature)="),  # signed URLs
    re.compile(r"data:image/[a-zA-Z]+;base64,"),  # embedded base64 image bytes
]

FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
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
)


def scan_for_pii(data: Any, path: str = "") -> list[str]:
    """Recursively checks that no forbidden PII or raw image payloads exist."""
    errors: list[str] = []

    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else str(k)
            if str(k).lower() in FORBIDDEN_KEYS:
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


def validate_evidence_record(
    record: dict[str, Any], disallow_synthetic: bool = True
) -> tuple[bool, list[str]]:
    """Validates an individual evidence record."""
    errors: list[str] = []

    required_fields = (
        "evidence_id",
        "type",
        "status",
        "collected_by",
        "collected_at",
        "source_file",
        "checksum",
    )
    for field in required_fields:
        val = record.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append(f"missing_required_field:{field}")

    ev_type = str(record.get("type", "")).strip().lower()
    if ev_type and ev_type not in ALLOWED_TYPES:
        errors.append(f"invalid_type:{ev_type}")

    status = str(record.get("status", "")).strip().lower()
    if status and status not in ALLOWED_STATUS:
        errors.append(f"invalid_status:{status}")

    collected_at = record.get("collected_at")
    if collected_at:
        try:
            datetime.fromisoformat(str(collected_at))
        except Exception:
            errors.append(f"invalid_iso_timestamp:{collected_at}")

    checksum = record.get("checksum")
    if checksum and not isinstance(checksum, str):
        errors.append("checksum_must_be_string")

    is_synthetic = bool(record.get("is_synthetic", False))
    if disallow_synthetic and is_synthetic:
        errors.append("synthetic_evidence_not_allowed")

    # Check PII
    pii_violations = scan_for_pii(record)
    errors.extend(pii_violations)

    return len(errors) == 0, errors


def validate_evidence_file(
    file_path: Path, disallow_synthetic: bool = True
) -> tuple[bool, list[str]]:
    """Validates an evidence file containing a record or list of records."""
    if not file_path.exists():
        return False, [f"file_not_found:{file_path}"]

    try:
        content = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"invalid_json:{exc}"]

    errors: list[str] = []
    if isinstance(content, list):
        if not content:
            errors.append("empty_evidence_list")
        for idx, item in enumerate(content):
            if not isinstance(item, dict):
                errors.append(f"invalid_record_at_index:{idx}")
                continue
            passed, record_errors = validate_evidence_record(
                item, disallow_synthetic=disallow_synthetic
            )
            for err in record_errors:
                errors.append(f"record[{idx}].{err}")
    elif isinstance(content, dict):
        passed, record_errors = validate_evidence_record(
            content, disallow_synthetic=disallow_synthetic
        )
        errors.extend(record_errors)
    else:
        errors.append("root_must_be_dict_or_list")

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RC13 Evidence File")
    parser.add_argument("--input", type=Path, required=True, help="Path to evidence JSON file")
    parser.add_argument(
        "--allow-synthetic", action="store_true", help="Allow synthetic evidence for tests"
    )
    args = parser.parse_args()

    passed, errors = validate_evidence_file(
        args.input, disallow_synthetic=not args.allow_synthetic
    )
    if passed:
        print("EVIDENCE VALIDATION: PASS")
    else:
        print(f"EVIDENCE VALIDATION: FAILED ({len(errors)} errors)")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
