"""Tests for session-based candidate caching and cache invalidation (Step 7.15)."""

import time
from uuid import uuid4

from fashx.discovery.session_cache import (
    get_cached_candidate_ids,
    invalidate_user_cache,
    set_cached_candidate_ids,
)


def test_session_candidate_cache_and_expiration() -> None:
    user_id = uuid4()
    session_id = "sess_123"
    candidates = [f"item_{i}" for i in range(40)]

    set_cached_candidate_ids(user_id, session_id, candidates, ttl=0.1)

    cached = get_cached_candidate_ids(user_id, session_id)
    assert cached == candidates

    # After expiry
    time.sleep(0.15)
    expired = get_cached_candidate_ids(user_id, session_id)
    assert expired is None


def test_positive_signal_invalidates_all_user_sessions() -> None:
    user_id = uuid4()
    set_cached_candidate_ids(user_id, "s1", ["a", "b"], ttl=60.0)
    set_cached_candidate_ids(user_id, "s2", ["c", "d"], ttl=60.0)

    # Another user's session
    other_user = uuid4()
    set_cached_candidate_ids(other_user, "s3", ["x", "y"], ttl=60.0)

    assert get_cached_candidate_ids(user_id, "s1") is not None
    assert get_cached_candidate_ids(user_id, "s2") is not None

    invalidated = invalidate_user_cache(user_id)
    assert invalidated == 2

    # user_id sessions gone
    assert get_cached_candidate_ids(user_id, "s1") is None
    assert get_cached_candidate_ids(user_id, "s2") is None

    # Other user preserved
    assert get_cached_candidate_ids(other_user, "s3") is not None
