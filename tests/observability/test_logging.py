import json
import logging
from uuid import uuid4

from fashx.core.logging import JsonFormatter
from fashx.observability.correlation import get_correlation_id, set_correlation_id
from fashx.observability.logging import CorrelationFilter


def test_correlation_filter_with_id():
    cid = uuid4()
    set_correlation_id(cid)
    assert get_correlation_id() == cid

    flt = CorrelationFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="test message",
        args=(),
        exc_info=None,
    )

    result = flt.filter(record)
    assert result is True
    assert getattr(record, "correlation_id", None) == str(cid)
    set_correlation_id(None)


def test_correlation_filter_without_id():
    set_correlation_id(None)
    assert get_correlation_id() is None

    flt = CorrelationFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=25,
        msg="test message",
        args=(),
        exc_info=None,
    )

    result = flt.filter(record)
    assert result is True
    assert getattr(record, "correlation_id", None) == "-"


def test_json_formatter_standard_schema():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="fashx.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=50,
        msg="http_request",
        args=(),
        exc_info=None,
    )
    record.service = "fashx-api"
    record.environment = "staging"
    record.app_version = "0.2.1"
    record.event = "http_request"
    record.request_id = "req-123"
    record.trace_id = "trace-456"
    record.method = "GET"
    record.route = "/api/v1/feed"
    record.status_code = 200
    record.duration_ms = 45.2

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["service"] == "fashx-api"
    assert parsed["environment"] == "staging"
    assert parsed["event"] == "http_request"
    assert parsed["request_id"] == "req-123"
    assert parsed["trace_id"] == "trace-456"
    assert parsed["method"] == "GET"
    assert parsed["route"] == "/api/v1/feed"
    assert parsed["status_code"] == 200
    assert parsed["duration_ms"] == 45.2
    assert "timestamp" in parsed


def test_json_formatter_legacy_alias_mapping():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="fashx.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=80,
        msg="legacy_call",
        args=(),
        exc_info=None,
    )
    record.status = 201
    record.latency = 99.4
    record.route_template = "/api/v1/items"

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["status_code"] == 201
    assert parsed["duration_ms"] == 99.4
    assert parsed["route"] == "/api/v1/items"
