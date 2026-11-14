# Request Correlation and Distributed Tracing Specification

## 1. Request ID Validation and Lifecycle

Every inbound HTTP request arriving at the FastAPI gateway passes through `RequestContextMiddleware`:
1. **Validation**: The inbound `X-Request-ID` header is validated against `^[A-Za-z0-9._-]{1,64}$`.
2. **Sanitization**: If the incoming header is absent, contains invalid characters, or exceeds 64 characters, a cryptographically secure UUID4 is generated.
3. **Context Binding**: The validated ID is set in Python `ContextVar` storage (`_request_id`) and attached to `request.state.request_id`.
4. **Header Echo**: Every HTTP response echoes the correlation ID via the `X-Request-ID` header.
5. **Context Clearance**: Request context is reliably cleared in a `finally` block, including on maintenance mode 503 early exits and unhandled server errors.

## 2. Distributed Tracing with W3C Trace Context

To follow requests across process boundaries into Celery workers, FashXStudio conforms to the W3C Trace Context standard:
- Header format: `00-<trace_id_32_hex>-<parent_id_16_hex>-<trace_flags_2_hex>` (e.g. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`).
- The gateway parses incoming `traceparent` headers or generates new ones via `backend/fashx/core/tracing.py`.
- Response headers return `traceparent` and `X-Trace-ID`.

## 3. Celery Task Header Propagation

When an API route dispatches a background task (e.g. Virtual Try-On or catalog ingestion), the dispatcher attaches correlation metadata to task headers:

```python
headers = {
    "request_id": get_request_id(),
    "trace_id": get_trace_id(),
    "traceparent": generate_traceparent(),
}
task.apply_async(
    args=[str(job_id)],
    headers=headers,
    ignore_result=True,
)
```

In the Celery worker, signal handlers in `backend/fashx/workers/signals.py` intercept `task_prerun`, extract `request_id` and `traceparent`, and re-establish the context so that all worker logs and Sentry events share the exact same correlation identifiers.
