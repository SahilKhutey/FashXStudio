# AI Fashion Assistant — Foundation 18

## Analytics & MVP Validation Instrumentation

Foundation 18 adds the first queryable MVP validation layer without introducing a separate analytics warehouse or daily-rollup table.

### Runtime model
- Durable product/system events remain in `domain_events`.
- Commerce, wardrobe, and feedback tables remain authoritative for their respective outcomes.
- The validation read model computes an aggregate snapshot over a requested time window.
- Session start/end events are recorded with a `session_id` in event payloads.
- The analytics dashboard endpoint is internal-service protected.

### Validation metrics
- try-on started/completed/failed
- result views
- retry requests
- feedback submissions
- wardrobe saves
- buy clicks
- unique and repeat try-on users
- unique and repeat session users
- completion/view/feedback/save/buy/repeat rates

### Rate definitions
- completion = completed / started
- result view = viewed / completed
- feedback = feedback submitted / completed
- save = wardrobe saves / completed
- buy click = buy clicks / completed
- repeat try-on = repeat try-on users / unique try-on users
- repeat session = repeat session users / unique session users

These are MVP diagnostic ratios, not causal attribution metrics.

### API
- `POST /api/v1/analytics/session-events` — authenticated mobile event ingestion for `session_started|session_ended`.
- `GET /api/v1/analytics/validation` — internal dashboard snapshot; defaults to the last 30 days.

### Scalability
Foundation 18 intentionally queries operational data directly. A future analytics warehouse or daily rollup can consume the same events without changing mobile contracts.
