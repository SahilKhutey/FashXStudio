"""Pagination management and protocol safeguards for catalog sources."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from urllib.parse import urlparse

from fashx.catalog.acquisition.http_client import validate_source_url


class PaginationError(Exception):
    """Base exception for pagination protocol violations."""


class RepeatedCursorError(PaginationError):
    """Raised when provider returns an identical cursor causing an infinite loop."""


class EmptyPageThresholdExceededError(PaginationError):
    """Raised when provider repeatedly returns empty pages with has_more=True."""


@dataclass
class PaginationState:
    """Tracks pagination state and detects cursor loops and empty page anomalies."""

    current_cursor: str | None = None
    has_more: bool = True
    page_size: int = 100
    pages_fetched: int = 0
    consecutive_empty_pages: int = 0
    seen_cursors: set[str] = field(default_factory=set)

    def advance(self, next_cursor: str | None, has_more: bool, items_count: int) -> None:
        """Advance pagination state with protocol validation."""
        self.pages_fetched += 1

        if items_count == 0:
            self.consecutive_empty_pages += 1
            if self.consecutive_empty_pages >= 3 and has_more:
                raise EmptyPageThresholdExceededError(
                    "Provider returned 3 consecutive empty pages with has_more=True."
                )
        else:
            self.consecutive_empty_pages = 0

        if next_cursor:
            if next_cursor in self.seen_cursors:
                raise RepeatedCursorError(
                    f"Protocol violation: Provider returned repeated cursor '{next_cursor}'."
                )
            self.seen_cursors.add(next_cursor)

        self.current_cursor = next_cursor
        self.has_more = has_more


def validate_pagination_url(
    next_url: str,
    allowed_hostnames: Sequence[str] = (),
    resolve_dns: bool = True,
) -> str:
    """Validate nextUrl pagination reference against scheme and host allowlist."""
    parsed = urlparse(next_url)
    if parsed.scheme.lower() != "https":
        raise PaginationError(f"Insecure pagination URL scheme '{parsed.scheme}'. Must be HTTPS.")

    host = parsed.hostname
    if not host:
        raise PaginationError(f"Invalid pagination URL: missing host in '{next_url}'.")

    # Re-use shared URL validation for SSRF checks
    return validate_source_url(
        next_url,
        allowed_hostnames=allowed_hostnames,
        require_https=True,
        resolve_dns=resolve_dns,
    )
