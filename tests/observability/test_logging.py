import logging
from uuid import uuid4

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
