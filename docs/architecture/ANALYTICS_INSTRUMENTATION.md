# FashXStudio — Backend Analytics Instrumentation & Pipeline Architecture

**Document ID:** `FASHX-ARCH-002`  
**Version:** `1.0 — Technical Baseline`  
**Date:** `10 November 2026`  
**Scope:** `Phase 01.5 — Backend Instrumentation & Real-Time Event Dispatch`  

---

## 1. Instrumentation Architecture Overview

To maintain API p95 latency under 500ms, analytics event ingestion **must never block HTTP request threads** or add synchronous database write overhead to shopper transactions.

```mermaid
flowchart LR
    Client["Mobile / Web Client"] -->|HTTP Request| API["FastAPI Gateway"]
    API -->|1. Transact| DB[("PostgreSQL Transaction")]
    API -->|2. Post-Commit Hook| Outbox["In-Memory Event Dispatcher"]
    Outbox -->|3. LPUSH| RedisQ[("Redis Event Stream")]
    RedisQ -->|4. Consumer| Worker["Celery Analytics Consumer"]
    Worker -->|5. Bulk INSERT| AnalyticsDB[("Partitioned analytics_events")]
    Worker -->|6. HINCRBY| RedisCache[("Real-Time Metric Rollups")]
    API -->>|HTTP 200 Response| Client
```

---

## 2. Transactional Event Dispatcher Pattern

Events are emitted strictly **after** database transactions successfully commit to prevent phantom events from rolled-back operations:

```python
# Conceptual Implementation: backend/fashx/observability/event_emitter.py
from datetime import UTC, datetime
from uuid import UUID, uuid4
from fashx.infrastructure.redis import get_redis_client

class EventEmitter:
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()

    async def emit_post_commit(
        self,
        event_name: str,
        session_id: UUID,
        shopper_id: UUID | None = None,
        merchant_id: UUID | None = None,
        product_id: UUID | None = None,
        properties: dict | None = None,
        is_internal: boolean = False,
    ) -> None:
        payload = {
            "event_id": str(uuid4()),
            "event_name": event_name,
            "event_version": 1,
            "occurred_at": datetime.now(UTC).isoformat(),
            "session_id": str(session_id),
            "shopper_id": str(shopper_id) if shopper_id else None,
            "merchant_id": str(merchant_id) if merchant_id else None,
            "product_id": str(product_id) if product_id else None,
            "is_internal": is_internal,
            "properties": properties or {},
        }
        # Fire-and-forget push to Redis stream (Latency < 2ms)
        await self.redis.xadd("stream:fashx:analytics", {"payload": json.dumps(payload)})
```

---

## 3. Real-Time Metric Counters via Redis

For high-frequency operational metrics (e.g. active daily impressions, instantaneous try-on job counts), workers execute atomic Redis hash operations:

```
REDIS KEY PATTERN: metrics:merchant:{merchant_id}:{YYYY-MM-DD}
HASH FIELDS:
  - impressions (HINCRBY)
  - vto_started (HINCRBY)
  - vto_completed (HINCRBY)
  - looks_saved (HINCRBY)
  - handoff_clicks (HINCRBY)
```

This guarantees sub-5ms read access for the merchant dashboard overview.
