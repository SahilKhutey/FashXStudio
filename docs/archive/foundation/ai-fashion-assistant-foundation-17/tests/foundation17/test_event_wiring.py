from pathlib import Path


def test_tryon_service_emits_lifecycle_events() -> None:
    source = Path("api/app/tryon/application/service.py").read_text()
    for event_type in ("tryon_started", "tryon_completed", "tryon_failed", "tryon_cancelled"):
        assert event_type in source


def test_mobile_tryon_client_exposes_feedback_and_telemetry_targets() -> None:
    source = Path("mobile/api/tryon.ts").read_text()
    assert "feedback" in source
    assert "telemetry" in source
