# RC-01 — Observability & Error Diagnostics

## Elimination of Silent Failures (FX-008)
Prior to RC-01, the core feed recommendation engine contained five broad `except Exception: pass` blocks in `backend/fashx/recommendation/application/generate_feed.py`.

### Identified Risks
1. Silent database schema mismatches would be treated as "user has no signals".
2. Connection pooling exhaustion or query timeout errors were invisible.
3. Cold-start failures could not be distinguished from users who simply had not performed any likes or saves.

### Remediation
1. Replaced all five `except Exception: pass` blocks with explicit error logging using the module logger:
   ```python
   try:
       # taste signal extraction
   except Exception as exc:
       logger.warning("Failed to extract taste vector for user %s: %s", user_id, exc, exc_info=True)
   ```
2. Unhandled critical exceptions (e.g. database disconnect during candidate querying) are allowed to propagate to FastAPI exception handlers, generating proper `500 Internal Server Error` responses with trace IDs rather than masking failures behind a fake empty feed.

## Diagnostic Schema (FX-009)
Feed responses now provide actionable empty feed diagnostics:
```python
if not candidates:
    empty_reason = "catalog_empty" if total_candidates == 0 else "all_candidates_filtered"
    return FeedResult(items=[], next_cursor=None, empty_reason=empty_reason)
```

### Mobile Handling of `empty_reason`
- `"catalog_empty"`: Informs user that the store catalog is currently updating.
- `"all_candidates_filtered"`: Displays an interactive prompt: *"No styles match your active budget and category filters. Adjust your budget or select more categories to see looks."*
