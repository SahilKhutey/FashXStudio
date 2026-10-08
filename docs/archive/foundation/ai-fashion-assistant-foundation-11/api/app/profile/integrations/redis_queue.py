from __future__ import annotations

import json
import uuid
from api.app.core.settings import get_settings


class RedisQueue:
    async def enqueue(self, *, queue: str, payload: dict) -> str:
        import redis.asyncio as redis

        client = redis.from_url(get_settings().redis_url, decode_responses=True)
        message_id = str(uuid.uuid4())
        body = {"message_id": message_id, **payload}
        await client.rpush(queue, json.dumps(body, separators=(",", ":")))
        await client.aclose()
        return message_id
