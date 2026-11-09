import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.rc13.validate_evidence import (
    validate_evidence_file,
    validate_evidence_record,
)


def sample_record(tmp_file: Path | None = None) -> dict[str, object]:
    fpath = str(tmp_file) if tmp_file else "docs/reengineering/RC13/11_TEST_PLAN.md"
    chk = "aff2809f06541d7b3c67d838f7b3fe64100b7e825198be8be634310f2547cf56"
    if tmp_file and tmp_file.exists():
        chk = hashlib.sha256(tmp_file.read_bytes()).hexdigest()

    return {
        "evidence_id": "EV-RC13-001",
        "type": "technical",
        "status": "pass",
        "collected_by": "qa_lead",
        "collected_at": "2026-11-08T10:00:00Z",
        "source_file": fpath,
        "checksum": chk,
        "is_synthetic": False,
    }


def test_valid_evidence_record_passes():
    record = sample_record()
    valid, errors = validate_evidence_record(record, disallow_synthetic=True, verify_source_file=True)
    assert valid is True
    assert not errors


def test_missing_required_field_fails():
    record = sample_record()
    del record["collected_by"]
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("missing_required_field:collected_by" in err for err in errors)


def test_placeholder_reviewer_fails():
    record = sample_record()
    record["collected_by"] = "unassigned"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("unauthorized_or_placeholder_reviewer" in err for err in errors)


def test_future_timestamp_fails():
    record = sample_record()
    record["collected_at"] = "2099-01-01T00:00:00Z"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("future_timestamp_not_allowed" in err for err in errors)


def test_checksum_mismatch_fails_authentication():
    with TemporaryDirectory() as tmp_dir:
        tmp_f = Path(tmp_dir) / "source.txt"
        tmp_f.write_text("authentic output", encoding="utf-8")
        record = sample_record(tmp_f)
        record["checksum"] = "badhash1234567890abcdef"

        valid, errors = validate_evidence_record(record, verify_source_file=True)
        assert valid is False
        assert any("checksum_mismatch" in err for err in errors)


def test_missing_source_file_fails_authentication():
    record = sample_record()
    record["source_file"] = "non_existent_output_file.txt"
    valid, errors = validate_evidence_record(record, verify_source_file=True)
    assert valid is False
    assert any("source_file_not_found" in err for err in errors)


def test_invalid_type_and_status():
    record = sample_record()
    record["type"] = "invalid_category"
    record["status"] = "partially_ok"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("invalid_type:invalid_category" in err for err in errors)
    assert any("invalid_status:partially_ok" in err for err in errors)


def test_pii_detection_rejects_email():
    record = sample_record()
    record["reviewer_contact"] = "tester@example.com"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("pii_pattern_match" in err for err in errors)


def test_synthetic_rejection_for_real_validation():
    record = sample_record()
    record["is_synthetic"] = True
    valid, errors = validate_evidence_record(record, disallow_synthetic=True)
    assert valid is False
    assert "synthetic_evidence_not_allowed" in errors

    # Allowed when explicitly permitted
    valid_synth, errors_synth = validate_evidence_record(record, disallow_synthetic=False)
    assert valid_synth is True
    assert not errors_synth


def test_validate_evidence_file():
    with TemporaryDirectory() as tmp_dir:
        fpath = Path(tmp_dir) / "evidence.json"
        data = [sample_record(), sample_record()]
        fpath.write_text(json.dumps(data), encoding="utf-8")

        valid, errors = validate_evidence_file(fpath, verify_source_files=True)
        assert valid is True
        assert not errors
