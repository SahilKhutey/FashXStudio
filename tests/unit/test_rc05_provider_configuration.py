import pytest
from fashx.core.dependencies import get_tryon_adapter
from fashx.core.settings import get_settings


def test_mock_provider_is_explicit_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "tryon_provider", "mock")
    monkeypatch.setattr(settings, "env", "dev")
    adapter = get_tryon_adapter()
    assert adapter.provider == "mock"
    assert adapter.is_commercial_cleared is False


def test_unknown_provider_does_not_silently_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "tryon_provider", "unknown_provider")
    monkeypatch.setattr(settings, "env", "dev")
    with pytest.raises((ValueError, RuntimeError, NotImplementedError), match="Unknown or unsupported"):
        get_tryon_adapter()


def test_self_hosted_provider_is_not_silently_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "tryon_provider", "fashn_selfhost")
    monkeypatch.setattr(settings, "env", "dev")
    with pytest.raises(NotImplementedError, match="fashn_selfhost try-on adapter is not implemented"):
        get_tryon_adapter()


def test_mock_adapter_rejected_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "tryon_provider", "mock")
    monkeypatch.setattr(settings, "env", "prod")
    with pytest.raises(RuntimeError, match="not allowed in production"):
        get_tryon_adapter()


def test_fashn_api_key_required_for_fashn_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "tryon_provider", "fashn_api")
    monkeypatch.setattr(settings, "fashn_api_key", None)
    monkeypatch.setattr(settings, "env", "dev")
    with pytest.raises(ValueError, match="FASHN_API_KEY required"):
        get_tryon_adapter()
