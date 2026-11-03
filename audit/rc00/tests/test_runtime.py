from pathlib import Path
from audit.rc00.runtime_audit import audit_runtime


def test_mock_provider_is_detected(tmp_path: Path):
    (tmp_path / ".env.example").write_text("TRYON_PROVIDER=mock\n", encoding="utf-8")
    result = audit_runtime(tmp_path)
    assert result["risk_checks"]["mock_tryon_default"] is True


def test_secret_values_are_not_returned(tmp_path: Path):
    (tmp_path / ".env.example").write_text("FASHN_API_KEY=example-secret\n", encoding="utf-8")
    result = audit_runtime(tmp_path)
    assert "example-secret" not in str(result)
    assert result["secret_values_exposed"] is False
