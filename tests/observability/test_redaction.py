import logging

from fashx.core.logging import RedactFilter, scrub


def test_scrub_dict_sensitive_keys():
    payload = {
        "user_id": "usr-123",
        "authorization": "Bearer secret-token",
        "token": "tok_12345",
        "password": "Password123!",
        "secret": "my-secret",
        "api_key": "key_9999",
        "cookie": "session=abc",
        "database_url": "postgresql+asyncpg://fashx:secret@localhost:5432/db",
        "redis_url": "redis://:secret@localhost:6379/0",
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "fashn_api_key": "fa_live_12345",
        "signed_url": "https://bucket.s3.amazonaws.com/image.jpg?X-Amz-Signature=abc",
        "body_measurements": {"bust": 34, "waist": 28},
        "skin_tone": "type-3",
        "email": "user@example.com",
        "phone": "+919876543210",
    }
    cleaned = scrub(payload)

    assert cleaned["user_id"] == "usr-123"
    assert cleaned["authorization"] == "[redacted]"
    assert cleaned["token"] == "[redacted]"
    assert cleaned["password"] == "[redacted]"
    assert cleaned["secret"] == "[redacted]"
    assert cleaned["api_key"] == "[redacted]"
    assert cleaned["cookie"] == "[redacted]"
    assert cleaned["database_url"] == "[redacted]"
    assert cleaned["redis_url"] == "[redacted]"
    assert cleaned["access_key"] == "[redacted]"
    assert cleaned["secret_access_key"] == "[redacted]"
    assert cleaned["fashn_api_key"] == "[redacted]"
    assert cleaned["signed_url"] == "[redacted]"
    assert cleaned["body_measurements"] == "[redacted]"
    assert cleaned["skin_tone"] == "[redacted]"
    assert cleaned["email"] == "[redacted]"
    assert cleaned["phone"] == "[redacted]"


def test_scrub_string_patterns():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    text_with_jwt = f"User logged in with token {jwt}"
    assert scrub(text_with_jwt) == "User logged in with token [redacted]"

    email_text = "Contact support at help@fashxstudio.com for assistance"
    assert scrub(email_text) == "Contact support at [redacted] for assistance"

    s3_url = "https://bucket.s3.amazonaws.com/pic.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Signature=abcdef0123456789"
    scrubbed_url = scrub(s3_url)
    assert "[redacted]" in scrubbed_url
    assert "abcdef0123456789" not in scrubbed_url

    b64_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgF"
    assert scrub(b64_image) == "[redacted]"


def test_scrub_nested_structures():
    nested = {
        "status": "ok",
        "items": [
            {"name": "shirt", "meta": {"token": "secret1"}},
            {"name": "pants", "meta": {"safe": "value"}},
        ],
        "tuple_data": ("user@test.com", "public_info"),
    }
    cleaned = scrub(nested)

    assert cleaned["items"][0]["meta"]["token"] == "[redacted]"
    assert cleaned["items"][1]["meta"]["safe"] == "value"
    assert cleaned["tuple_data"][0] == "[redacted]"
    assert cleaned["tuple_data"][1] == "public_info"


def test_redact_filter():
    flt = RedactFilter()
    record = logging.LogRecord(
        name="fashx.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=80,
        msg="Credentials: password=SuperSecret123! and email=founder@fashx.com",
        args=(),
        exc_info=None,
    )
    record.secret_field = "SuperSecretToken"

    flt.filter(record)
    assert "founder@fashx.com" not in record.msg
    assert "[redacted]" in record.msg
    assert getattr(record, "secret_field", None) == "SuperSecretToken"  # not in sensitive keys unless dict
