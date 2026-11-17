"""CloudWatch Embedded Metric Format (EMF) operational metrics generator.

Emits structured JSON metrics to stdout in the CloudWatch Embedded Metric Format.
When collected by the Amazon ECS CloudWatch log driver, CloudWatch automatically extracts
custom high-resolution metrics without requiring a separate metric collection agent.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

logger = logging.getLogger("fashx.metrics")

# High-cardinality keys prohibited from metric dimensions to protect against CloudWatch cost runaway
PROHIBITED_DIMENSION_KEYS = {
    "request_id",
    "trace_id",
    "user_id",
    "job_id",
    "vendor_job_id",
    "product_id",
    "source_id",
    "url",
    "email",
    "key",
    "object_key",
    "exception",
    "error",
    "error_message",
}


def emit_metric(
    name: str,
    value: float,
    unit: str = "None",
    *,
    service: str = "api",
    environment: str = "dev",
    dimensions: dict[str, str] | None = None,
    namespace: str = "FashX/Application",
) -> dict[str, Any]:
    """Emit an operational metric formatted as a CloudWatch Embedded Metric Format (EMF) event.

    Args:
        name: Name of the metric (e.g. RequestLatency, StorageUploadCount)
        value: Numeric measurement value
        unit: CloudWatch metric unit (Seconds, Milliseconds, Bytes, Count, etc.)
        service: Originating service (api, tryon, ingest, beat, storage)
        environment: Deployment environment (dev, staging, production)
        dimensions: Low-cardinality dimension key-value pairs
        namespace: CloudWatch Metrics namespace
    """
    safe_dimensions: dict[str, str] = {
        "Service": service,
        "Environment": environment,
    }

    if dimensions:
        for k, v in dimensions.items():
            if str(k).lower() in PROHIBITED_DIMENSION_KEYS:
                continue
            safe_dimensions[k] = str(v)

    dimension_keys = sorted(safe_dimensions.keys())
    now_ms = int(time.time() * 1000)

    # CloudWatch Embedded Metric Format document specification
    emf_event: dict[str, Any] = {
        "_aws": {
            "Timestamp": now_ms,
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace,
                    "Dimensions": [dimension_keys],
                    "Metrics": [
                        {
                            "Name": name,
                            "Unit": unit,
                        }
                    ],
                }
            ],
        },
        **safe_dimensions,
        name: value,
    }

    logger.info(json.dumps(emf_event, ensure_ascii=False))
    return emf_event
