import json
from pathlib import Path

from scripts.vto.phase0_preflight import (
    REQUIRED_PATHS,
    build_report,
)


def make_repository(root: Path) -> Path:
    """Create a minimal fake repository for isolated unit tests."""
    for relative in REQUIRED_PATHS:
        path = root / relative
        if relative.endswith(".py") or "." in Path(relative).name:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# test fixture\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
    return root


def test_required_repository_files_exist(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    report = build_report(root, environ={})
    assert report["repository_paths_ok"] is True
    assert report["missing_paths"] == []


def test_missing_repository_paths_reported(tmp_path: Path) -> None:
    # Empty directory - all paths should be missing
    report = build_report(tmp_path, environ={})
    assert report["repository_paths_ok"] is False
    assert len(report["missing_paths"]) == len(REQUIRED_PATHS)
    for p in REQUIRED_PATHS:
        assert p in report["missing_paths"]


def test_default_provider_is_reported_as_mock(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    report = build_report(root, environ={})
    assert report["repository_paths_ok"] is True
    assert report["provider"] == "mock"
    assert report["live_inference_verified"] is False
    assert any(
        "Mock provider selected" in issue for issue in report["configuration_issues"]
    )


def test_hosted_provider_without_key_is_reported(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    report = build_report(root, environ={"TRYON_PROVIDER": "fashn_api", "FASHN_API_KEY": ""})
    assert report["provider"] == "fashn_api"
    assert report["has_api_key"] is False
    assert any(
        "FASHN_API_KEY is missing" in issue for issue in report["configuration_issues"]
    )


def test_hosted_provider_with_key_is_reported(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    report = build_report(
        root,
        environ={"TRYON_PROVIDER": "fashn_api", "FASHN_API_KEY": "dummy_secret_key"},
    )
    assert report["provider"] == "fashn_api"
    assert report["has_api_key"] is True
    assert not any(
        "FASHN_API_KEY is missing" in issue for issue in report["configuration_issues"]
    )


def test_production_uses_mock_provider_reported(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    report = build_report(
        root,
        environ={"ENV": "prod", "TRYON_PROVIDER": "mock"},
    )
    assert report["is_prod"] is True
    assert any(
        "Production environment cannot use mock provider" in issue
        for issue in report["configuration_issues"]
    )


def test_secret_redaction(tmp_path: Path) -> None:
    root = make_repository(tmp_path)
    secret_token = "ultra_sensitive_fashn_credential_secret_999"
    report = build_report(
        root,
        environ={"TRYON_PROVIDER": "fashn_api", "FASHN_API_KEY": secret_token},
    )
    serialized = json.dumps(report)
    assert secret_token not in serialized
    assert report["has_api_key"] is True
