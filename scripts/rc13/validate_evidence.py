"""RC13 Evidence validator, quarantine verifier, and authentication engine."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ALLOWED_STATUS: frozenset[str] = frozenset({"pass", "fail", "unknown", "in_progress"})
ALLOWED_TYPES: frozenset[str] = frozenset(
    {"technical", "product", "market", "vto", "catalog", "compliance", "security"}
)

FORBIDDEN_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),  # email
    re.compile(r"(?<!\w)(?:\+91|0)?[6-9]\d{9}(?!\w)"),  # phone number
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

DISALLOWED_REVIEWERS: frozenset[str] = frozenset(
    {"", "unassigned", "test", "tester", "dummy", "unknown", "nobody", "placeholder"}
)

PII_EXEMPT_KEYS: frozenset[str] = frozenset(
    {"checksum", "sha256", "evidence_id", "source_file"}
)


def scan_for_pii(data: Any, path: str = "") -> list[str]:
    """Recursively checks that no forbidden PII or raw image payloads exist."""
    errors: list[str] = []

    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else str(k)
            if str(k).lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{current_path}")
            if str(k).lower() in PII_EXEMPT_KEYS:
                continue
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


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_evidence_record(
    record: dict[str, Any],
    disallow_synthetic: bool = True,
    verify_source_file: bool = False,
) -> tuple[bool, list[str]]:
    """Validates and authenticates an individual evidence record.

    Authentication includes:
    1. Required field schema completeness.
    2. Valid status and type enumerations.
    3. Authorized human reviewer (non-placeholder).
    4. Valid UTC ISO timestamp not in future.
    5. Synthetic data rejection for release governance.
    6. Quarantine PII scanning.
    7. Cryptographic checksum verification against actual source file when verify_source_file=True.
    """
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

    collected_by = str(record.get("collected_by", "")).strip().lower()
    if collected_by in DISALLOWED_REVIEWERS:
        errors.append(f"unauthorized_or_placeholder_reviewer:{collected_by}")

    collected_at = record.get("collected_at")
    if collected_at:
        try:
            dt = datetime.fromisoformat(str(collected_at))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            now = datetime.now(UTC)
            if dt > now:
                errors.append(f"future_timestamp_not_allowed:{collected_at}")
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

    # Cryptographic file authentication
    if verify_source_file:
        src_path_str = record.get("source_file")
        if src_path_str:
            src_path = Path(str(src_path_str))
            if not src_path.exists():
                errors.append(f"source_file_not_found:{src_path}")
            elif checksum:
                actual_hash = compute_sha256(src_path)
                expected_hash = str(checksum).lower().replace("sha256:", "").strip()
                if actual_hash != expected_hash:
                    # Also check normalized line-ending digest for cross-platform git checkout resilience
                    is_line_ending_match = False
                    try:
                        raw_bytes = src_path.read_bytes()
                        crlf_hash = hashlib.sha256(
                            raw_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                        ).hexdigest()
                        lf_hash = hashlib.sha256(raw_bytes.replace(b"\r\n", b"\n")).hexdigest()
                        if expected_hash in (crlf_hash, lf_hash):
                            is_line_ending_match = True
                    except Exception:
                        pass

                    if not is_line_ending_match:
                        errors.append(
                            f"checksum_mismatch:expected_{expected_hash}_got_{actual_hash}"
                        )

    return len(errors) == 0, errors


def validate_evidence_file(
    file_path: Path,
    disallow_synthetic: bool = True,
    verify_source_files: bool = False,
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
                item,
                disallow_synthetic=disallow_synthetic,
                verify_source_file=verify_source_files,
            )
            for err in record_errors:
                errors.append(f"record[{idx}].{err}")
    elif isinstance(content, dict):
        passed, record_errors = validate_evidence_record(
            content,
            disallow_synthetic=disallow_synthetic,
            verify_source_file=verify_source_files,
        )
        errors.extend(record_errors)
    else:
        errors.append("root_must_be_dict_or_list")

    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate & Authenticate RC13 Evidence File")
    parser.add_argument("--input", type=Path, required=True, help="Path to evidence JSON file")
    parser.add_argument(
        "--allow-synthetic", action="store_true", help="Allow synthetic evidence for tests"
    )
    parser.add_argument(
        "--verify-files", action="store_true", help="Verify existence and SHA-256 checksums of source files"
    )
    args = parser.parse_args()

    passed, errors = validate_evidence_file(
        args.input,
        disallow_synthetic=not args.allow_synthetic,
        verify_source_files=args.verify_files,
    )
    if passed:
        print("EVIDENCE VALIDATION & AUTHENTICATION: PASS")
    else:
        print(f"EVIDENCE VALIDATION & AUTHENTICATION: FAILED ({len(errors)} errors)")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
