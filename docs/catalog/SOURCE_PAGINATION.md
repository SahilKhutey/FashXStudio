# Source Pagination Framework

## 1. Overview and Protocol Hazards

Catalog sources expose a variety of pagination paradigms:
- Cursor-based pagination (`next_cursor`, `continuation_token`)
- Page-number and offset-based pagination (`page=2`, `offset=100`)
- Link-header or `next_url` pagination

Without strict bounds, external feeds can lead to critical operational failures:
1. **Infinite Cursor Cycles**: Upstream services occasionally return a previously seen cursor, looping infinitely.
2. **Ghost Feeds (Empty Pages)**: Feeds returning 0 products with `has_more=True` indefinitely.
3. **SSRF via `next_url`**: An attacker or rogue feed providing a `next_url` targeting internal metadata services or intranet IPs.

## 2. Pagination State Tracking

The `PaginationState` class (`backend/fashx/catalog/acquisition/pagination.py`) provides safe advancement:

```python
@dataclass
class PaginationState:
    current_cursor: str | None = None
    has_more: bool = True
    page_size: int = 100
    pages_fetched: int = 0
    consecutive_empty_pages: int = 0
    seen_cursors: set[str] = field(default_factory=set)

    def advance(self, next_cursor: str | None, has_more: bool, items_count: int) -> None: ...
```

## 3. Safeguards Implemented

- **Repeated Cursor Detection**: Every non-null cursor is tracked in `seen_cursors`. If an identical cursor is received, `RepeatedCursorError` is raised immediately.
- **Empty Page Bounding**: If 3 consecutive pages return 0 products while claiming `has_more=True`, `EmptyPageThresholdExceededError` terminates the run.
- **Pagination URL Validation**: Any `next_url` pagination link is parsed via `validate_pagination_url()`, requiring:
  - Scheme must be HTTPS.
  - Hostname must match the source's approved host allowlist.
  - The destination IP must pass SSRF filtering.
