from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from api.app.feed.domain.ranking import feed_reasons
from schemas.feed.cursor import InvalidFeedCursor, decode_feed_cursor, encode_feed_cursor


def test_feed_cursor_round_trip():
    created_at = datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc)
    garment_id = uuid4()
    encoded = encode_feed_cursor(created_at=created_at, garment_id=garment_id)
    decoded_time, decoded_id = decode_feed_cursor(encoded)
    assert decoded_time == created_at
    assert decoded_id == garment_id


def test_feed_cursor_rejects_invalid_value():
    with pytest.raises(InvalidFeedCursor):
        decode_feed_cursor("not-a-valid-cursor")


def test_feed_reasons_are_deterministic():
    assert feed_reasons() == ["curated", "new_arrival"]
    assert feed_reasons(category_filtered=True, price_filtered=True) == [
        "curated",
        "new_arrival",
        "category_match",
        "budget_match",
    ]
