from __future__ import annotations

import base64
import time
from uuid import UUID


class InvalidCursorError(ValueError):
    """Raised when an opaque pagination cursor is malformed, invalid, or expired."""


def generate_cursor_token(session_id: UUID, offset: int) -> str:
    """Generate an opaque base64 cursor token encoding session and offset position."""
    ts = int(time.time())
    raw = f"{session_id}:{offset}:{ts}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor_token(cursor_str: str, max_age_seconds: int = 3600) -> tuple[UUID, int]:
    """Decode and validate an opaque pagination cursor.

    Returns:
        tuple of (session_id, offset)

    Raises:
        InvalidCursorError: If token is malformed, negative offset, or expired.
    """
    if not cursor_str:
        raise InvalidCursorError("Cursor string is empty")

    try:
        raw_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        raw = raw_bytes.decode("utf-8")
        parts = raw.split(":")
        if len(parts) != 3:
            raise InvalidCursorError("Malformed cursor token structure")

        session_id = UUID(parts[0])
        offset = int(parts[1])
        ts = int(parts[2])

        if offset < 0:
            raise InvalidCursorError("Offset cannot be negative")

        # Verify freshness
        now = int(time.time())
        if now - ts > max_age_seconds:
            raise InvalidCursorError("Cursor token has expired")

        return session_id, offset
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidCursorError(f"Invalid cursor token: {exc}") from exc


__all__ = [
    "InvalidCursorError",
    "decode_cursor_token",
    "generate_cursor_token",
]
