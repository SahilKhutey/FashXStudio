import io
import json
import logging

from fashx.core.logging import (
    JsonFormatter,
    RedactFilter,
    log_pd_access,
    scrub,
)


def test_scrub_jwt_token():
    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    msg = f"User logged in with token {fake_jwt} successfully"
    scrubbed = scrub(msg)
    assert fake_jwt not in scrubbed
    assert "[redacted]" in scrubbed


def test_scrub_presigned_url():
    presigned_url = "https://fashx-bucket.s3.ap-south-1.amazonaws.com/raw.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAEXAMPLE%2F20261011%2Fap-south-1%2Fs3%2Faws4_request&X-Amz-Signature=d2f9b88a9c80123456789abcdef"
    scrubbed = scrub(presigned_url)
    assert "AKIAEXAMPLE" not in scrubbed
    assert "d2f9b88a9c80123456789abcdef" not in scrubbed
    assert "[redacted]" in scrubbed


def test_scrub_email_address():
    msg = "Password reset requested for priya.sharma@example.com and rahul+pilot@domain.co.in"
    scrubbed = scrub(msg)
    assert "priya.sharma@example.com" not in scrubbed
    assert "rahul+pilot@domain.co.in" not in scrubbed
    assert "[redacted]" in scrubbed


def test_scrub_base64_payload():
    b64_img = "data:image/jpeg;base64," + "A" * 500
    scrubbed = scrub(b64_img)
    assert "data:image/jpeg;base64," not in scrubbed
    assert "[redacted]" in scrubbed


def test_scrub_dict_sensitive_keys():
    data = {
        "user_id": "usr-123",
        "authorization": "Bearer secret_token_12345",
        "apiKey": "ak_live_xyz987",
        "password": "MySuperSecretPassword!123",
        "nested": {
            "email": "test@fashx.studio",
            "token": "tok_abc_999",
        },
    }
    scrubbed = scrub(data)
    assert scrubbed["user_id"] == "usr-123"
    assert scrubbed["authorization"] == "[redacted]"
    assert scrubbed["password"] == "[redacted]"
    assert scrubbed["nested"]["email"] == "[redacted]"
    assert scrubbed["nested"]["token"] == "[redacted]"


def test_logger_redact_filter_and_json_formatter():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactFilter())

    logger = logging.getLogger("test.redaction.audit")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    email = "leaked_user@fashx.com"
    logger.info(f"Failed authentication for {email} with auth {fake_jwt}", extra={"request_id": "req-001"})

    output = stream.getvalue().strip()
    assert output, "Expected log output"
    entry = json.loads(output)

    assert entry["level"] == "INFO"
    assert entry["request_id"] == "req-001"
    assert email not in entry["message"]
    assert fake_jwt not in entry["message"]
    assert "[redacted]" in entry["message"]


def test_log_pd_access_audit():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactFilter())

    audit_logger = logging.getLogger("fashx.audit.pd_access")
    audit_logger.handlers.clear()
    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.INFO)

    log_pd_access(
        actor="admin:support_agent_01",
        user_id="usr_882049102",
        action="view_profile_for_erasure_request",
        purpose="DPDP Section 12 erasure verification",
    )

    output = stream.getvalue().strip()
    assert output, "Expected audit log output"
    entry = json.loads(output)

    assert entry["logger"] == "fashx.audit.pd_access"
    assert entry["user_id"] == "usr_882049102"
    assert "pd_access" in entry
    assert entry["pd_access"]["actor"] == "admin:support_agent_01"
    assert entry["pd_access"]["action"] == "view_profile_for_erasure_request"
