from __future__ import annotations

import base64
import json
from datetime import datetime
from uuid import UUID


class InvalidFeedCursor(ValueError):
    pass


def encode_feed_cursor(*, created_at: datetime, garment_id: UUID) -> str:
    payload = {"created_at": created_at.isoformat(), "id": str(garment_id)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_feed_cursor(value: str) -> tuple[datetime, UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        created_at = datetime.fromisoformat(payload["created_at"])
        garment_id = UUID(payload["id"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidFeedCursor("Invalid feed cursor") from exc
    if created_at.tzinfo is None:
        raise InvalidFeedCursor("Feed cursor timestamp must include timezone")
    return created_at, garment_id
