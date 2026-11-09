import json
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.rc13.validate_evidence import (
    validate_evidence_file,
    validate_evidence_record,
)


def sample_record() -> dict[str, object]:
    return {
        "evidence_id": "EV-RC13-001",
        "type": "technical",
        "status": "pass",
        "collected_by": "qa-engineer",
        "collected_at": "2026-11-09T10:00:00Z",
        "source_file": "docs/evidence/test_evidence.md",
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "is_synthetic": False,
    }


def test_valid_evidence_record_passes():
    record = sample_record()
    valid, errors = validate_evidence_record(record, disallow_synthetic=True)
    assert valid is True
    assert not errors


def test_missing_required_field_fails():
    record = sample_record()
    del record["collected_by"]
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("missing_required_field:collected_by" in err for err in errors)


def test_invalid_type_and_status():
    record = sample_record()
    record["type"] = "invalid_category"
    record["status"] = "partially_ok"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("invalid_type:invalid_category" in err for err in errors)
    assert any("invalid_status:partially_ok" in err for err in errors)


def test_invalid_iso_timestamp():
    record = sample_record()
    record["collected_at"] = "yesterday afternoon"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("invalid_iso_timestamp" in err for err in errors)


def test_pii_detection_rejects_email():
    record = sample_record()
    record["reviewer_contact"] = "tester@example.com"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("pii_pattern_match" in err for err in errors)


def test_pii_detection_rejects_forbidden_key():
    record = sample_record()
    record["raw_photo"] = "dummy_data"
    valid, errors = validate_evidence_record(record)
    assert valid is False
    assert any("forbidden_key" in err for err in errors)


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

        valid, errors = validate_evidence_file(fpath)
        assert valid is True
        assert not errors


def test_validate_evidence_file_not_found():
    valid, errors = validate_evidence_file(Path("non_existent_file_path.json"))
    assert valid is False
    assert any("file_not_found" in err for err in errors)
