import sys
from types import SimpleNamespace

from fashx.core.observability import _sentry_before_send, configure_sentry


def test_sentry_before_send_sanitizes_pii_and_credentials():
    event = {
        "request": {
            "url": "https://api.fashx.com/upload?X-Amz-Signature=secret123",
            "headers": {
                "Authorization": "Bearer super-secret-jwt",
                "Cookie": "session=sensitive_data",
                "User-Agent": "MobileApp/1.0",
            },
            "data": {"person_photo": "base64encodedbytes", "user_id": "123"},
        },
        "exception": {
            "values": [
                {"value": "Database connection error to postgresql://fashx:secret@db:5432/db failed"}
            ]
        },
    }

    sanitized = _sentry_before_send(event, {})
    assert sanitized is not None

    req = sanitized["request"]
    assert "secret123" not in req["url"]
    assert req["headers"]["Authorization"] == "[redacted]"
    assert req["headers"]["Cookie"] == "[redacted]"
    assert req["headers"]["User-Agent"] == "MobileApp/1.0"
    assert req["data"] == "[redacted]"

    exc_val = sanitized["exception"]["values"][0]["value"]
    assert "secret@db:5432" not in exc_val
    assert "[redacted]" in exc_val


def test_configure_sentry_without_dsn_does_not_initialize(monkeypatch):
    initialized = False

    class MockSentry:
        def init(self, **kwargs):
            nonlocal initialized
            initialized = True

    if "sentry_sdk" in sys.modules:
        monkeypatch.setattr("sys.modules", {"sentry_sdk": MockSentry(), **sys.modules})

    settings = SimpleNamespace(
        sentry_dsn=None,
        sentry_environment="test",
        app_version="0.2.0",
        is_production=False,
    )
    configure_sentry(settings)
    assert not initialized
