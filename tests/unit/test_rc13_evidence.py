import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.rc13.validate_evidence import (
    validate_evidence_file,
    validate_evidence_record,
)


def sample_record(tmp_file: Path | None = None) -> dict[str, object]:
    if tmp_file:
        fpath = str(tmp_file)
        chk = (
            hashlib.sha256(tmp_file.read_bytes()).hexdigest()
            if tmp_file.exists()
            else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
    else:
        target = Path("docs/reengineering/RC13/11_TEST_PLAN.md")
        fpath = str(target)
        if target.exists():
            chk = hashlib.sha256(target.read_bytes()).hexdigest()
        else:
            chk = "aff2809f06541d7b3c67d838f7b3fe64100b7e825198be8be634310f2547cf56"

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


def test_checksum_resilience_to_cross_platform_line_endings():
    with TemporaryDirectory() as tmp_dir:
        tmp_f = Path(tmp_dir) / "source.txt"
        tmp_f.write_bytes(b"line 1\r\nline 2\r\n")
        lf_hash = hashlib.sha256(b"line 1\nline 2\n").hexdigest()
        record = sample_record(tmp_f)
        record["checksum"] = lf_hash

        valid, errors = validate_evidence_record(record, verify_source_file=True)
        assert valid is True
        assert not errors


def test_validate_evidence_file():
    with TemporaryDirectory() as tmp_dir:
        src_file = Path(tmp_dir) / "source.md"
        src_file.write_text("# Test Plan\nVerified.", encoding="utf-8")
        fpath = Path(tmp_dir) / "evidence.json"
        data = [sample_record(src_file), sample_record(src_file)]
        fpath.write_text(json.dumps(data), encoding="utf-8")

        valid, errors = validate_evidence_file(fpath, verify_source_files=True)
        assert valid is True
        assert not errors
