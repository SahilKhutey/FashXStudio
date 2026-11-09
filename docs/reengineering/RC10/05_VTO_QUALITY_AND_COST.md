# RC10-E: VTO Quality, Reliability and Cost

## 1. Objectives
Virtual Try-On (VTO) is the core product differentiator. RC10 establishes strict provider provenance, fail-closed image validation, timeout recovery, and per-job cost instrumentation.

## 2. Provider Provenance Contract
Every completed try-on job record must store:
- `provider`: Target provider name (e.g. `fashn`).
- `model_version`: Exact model or endpoint tag used for inference.
- `duration_ms`: Wall-clock inference duration in milliseconds.
- `cost_estimate_usd`: Actual API credit or unit cost incurred.
- `is_mock`: Boolean flag explicitly indicating mock/synthetic execution.

## 3. Production Environment Restrictions
In staging and production, mock try-on providers are strictly forbidden by `validate_release_config()`. If an unapproved mock provider is configured in production, the application fails to start at initialization.

## 4. Quality & Safety Controls
- **Explicit Consent**: VTO execution requires explicit, recorded image processing consent (`consent_records`).
- **Fail-Closed Pre-validation**: Garments incompatible with try-on (accessories, non-tryon items) or corrupt image payloads are rejected prior to vendor dispatch.
- **Idempotent Queueing**: Duplicate submissions return the existing active job ID rather than spawning duplicate billable external API requests.
