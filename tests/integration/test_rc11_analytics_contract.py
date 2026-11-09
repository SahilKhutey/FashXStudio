"""RC11 Analytics and pilot export integration test."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fashx.api.v1.analytics import ProductJourneyEvent
from scripts.rc11.validate_pilot_data import validate_pilot_export


def test_product_journey_event_schema_contract():
    event = ProductJourneyEvent(
        event_id=uuid4(),
        event_name="feed_viewed",
        occurred_at=datetime.now(UTC),
        schema_version=1,
    )
    assert event.event_name == "feed_viewed"
    assert event.schema_version == 1
    assert event.tryon_job_id is None


def test_pilot_data_validator_detects_pii(tmp_path: Path):
    # Snapshot containing leaked email and phone
    leaked_data = {
        "metadata": {
            "pilot_id": "p1",
            "period_start": "2026-11-16T00:00:00Z",
            "period_end": "2026-12-07T23:59:59Z",
            "extracted_at": "2026-12-08T08:00:00Z",
            "evidence_type": "real",
            "source_reference": "ref-1",
        },
        "user_leak": {
            "contact": "user@example.com",
            "phone_num": "9876543210",
        },
    }
    test_file = tmp_path / "leaked_snapshot.json"
    test_file.write_text(json.dumps(leaked_data), encoding="utf-8")

    passed, errors = validate_pilot_export(test_file)
    assert not passed
    assert any("pii_pattern_match" in err for err in errors)


def test_pilot_data_validator_detects_measurement_keys(tmp_path: Path):
    measurement_data = {
        "metadata": {
            "pilot_id": "p1",
            "period_start": "2026-11-16T00:00:00Z",
            "period_end": "2026-12-07T23:59:59Z",
            "extracted_at": "2026-12-08T08:00:00Z",
            "evidence_type": "real",
            "source_reference": "ref-1",
        },
        "profile": {
            "waist_cm": 76.5,
        },
    }
    test_file = tmp_path / "measurement_snapshot.json"
    test_file.write_text(json.dumps(measurement_data), encoding="utf-8")

    passed, errors = validate_pilot_export(test_file)
    assert not passed
    assert any("forbidden_key:profile.waist_cm" in err for err in errors)
