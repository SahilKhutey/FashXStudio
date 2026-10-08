from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from fashx.domain.analytics.entities import (
    AnalyticsEvent,
)
from fashx.domain.analytics.enums import (
    AnalyticsEventType,
    AnalyticsSource,
)


def test_event_requires_identity():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED
    )
    with pytest.raises(ValidationError, match="requires customer_id or session_id"):
        event.validate()


def test_valid_session_event():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        session_id="session-1",
    )
    event.validate()
    assert event.session_id == "session-1"
    assert event.event_type == AnalyticsEventType.PRODUCT_VIEWED


def test_valid_customer_event():
    cid = uuid4()
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.PRODUCT_VIEWED,
        customer_id=cid,
    )
    event.validate()
    assert event.customer_id == cid


def test_negative_value_rejected():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.ORDER_COMPLETED,
        session_id="session-1",
        value=Decimal("-10"),
    )
    with pytest.raises(ValidationError, match="cannot be negative"):
        event.validate()


def test_invalid_currency_rejected():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.ORDER_COMPLETED,
        session_id="session-1",
        value=Decimal("100"),
        currency="USDD",
    )
    with pytest.raises(ValidationError, match="3-character code"):
        event.validate()


def test_valid_event_with_properties_and_source():
    event = AnalyticsEvent(
        event_type=AnalyticsEventType.SEARCH_PERFORMED,
        session_id="session-42",
        source=AnalyticsSource.WEB,
        properties={"query": "silk scarf", "position": "1"},
        region="IN",
        category="accessories",
    )
    event.validate()
    assert event.properties["query"] == "silk scarf"
    assert event.region == "IN"
    assert event.source == AnalyticsSource.WEB
