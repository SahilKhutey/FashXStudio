"""SA-006, SA-007, SA-008, SA-009: Pagination framework and loop prevention."""

from __future__ import annotations

import pytest

from fashx.catalog.acquisition.http_client import SecurityViolationError
from fashx.catalog.acquisition.pagination import (
    EmptyPageThresholdExceededError,
    PaginationError,
    PaginationState,
    RepeatedCursorError,
    validate_pagination_url,
)


def test_sa_006_pagination_state_advance() -> None:
    """SA-006: Normal cursor pagination advances correctly."""
    state = PaginationState(page_size=50)
    assert state.pages_fetched == 0
    assert state.has_more is True

    state.advance(next_cursor="cursor_page_2", has_more=True, items_count=50)
    assert state.pages_fetched == 1
    assert state.current_cursor == "cursor_page_2"
    assert state.has_more is True

    state.advance(next_cursor=None, has_more=False, items_count=20)
    assert state.pages_fetched == 2
    assert state.has_more is False


def test_sa_008_repeated_cursor_detection() -> None:
    """SA-008: Bounded loop prevention raises RepeatedCursorError on cycle."""
    state = PaginationState()
    state.advance(next_cursor="cursor_abc", has_more=True, items_count=10)
    state.advance(next_cursor="cursor_def", has_more=True, items_count=10)

    with pytest.raises(RepeatedCursorError) as exc_info:
        state.advance(next_cursor="cursor_abc", has_more=True, items_count=10)
    assert "repeated cursor" in str(exc_info.value).lower()
    assert "cursor_abc" in str(exc_info.value)


def test_sa_009_empty_page_threshold_bounding() -> None:
    """SA-009: Bounded consecutive empty pages terminates loop."""
    state = PaginationState()
    state.advance(next_cursor="cursor_1", has_more=True, items_count=0)
    state.advance(next_cursor="cursor_2", has_more=True, items_count=0)

    with pytest.raises(EmptyPageThresholdExceededError) as exc_info:
        state.advance(next_cursor="cursor_3", has_more=True, items_count=0)
    assert "empty pages" in str(exc_info.value).lower()


def test_pagination_url_validation() -> None:
    """Validate nextUrl allowlist preventing redirect loops or SSRF in pagination links."""
    allowed = ["api.merchant.com"]

    # Valid allowed host absolute url (without DNS resolution)
    valid_url = validate_pagination_url(
        "https://api.merchant.com/v1/products?page=2",
        allowed_hostnames=allowed,
        resolve_dns=False,
    )
    assert valid_url == "https://api.merchant.com/v1/products?page=2"

    # Insecure HTTP fails
    with pytest.raises(PaginationError) as exc_http:
        validate_pagination_url(
            "http://api.merchant.com/v1/products?page=2",
            allowed_hostnames=allowed,
            resolve_dns=False,
        )
    assert "Must be HTTPS" in str(exc_http.value)

    # Disallowed host change fails
    with pytest.raises(SecurityViolationError) as exc_host:
        validate_pagination_url(
            "https://attacker.com/v1/products?page=2",
            allowed_hostnames=allowed,
            resolve_dns=False,
        )
    assert "not in the approved source host allowlist" in str(exc_host.value)
