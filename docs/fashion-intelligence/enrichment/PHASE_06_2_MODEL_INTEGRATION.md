# Phase 06.2 — AI Model Integration and Provider Gateway

## 1. Gateway Design

The `ModelGateway` abstracts external and self-hosted AI models behind a consistent interface (`TextEnrichmentProvider` and `VisionEnrichmentProvider`).

```mermaid
flowchart TD
    Orch["Enrichment Orchestrator"] --> GW["ModelGateway"]
    GW --> Mock["MockTextEnrichmentProvider (Test/CI)"]
    GW --> LLM["Cloud LLM / Vision Model Adapter"]
    GW --> Local["Self-Hosted Model Adapter"]
    GW --> Timeout["Timeout & Bounded Retry Handler"]
    GW --> PolicyCheck["Strict Policy & Output Filter"]
```

## 2. Anti-Hallucination Prompt Architecture

- All merchant fields are treated as untrusted data inputs, not instructions.
- System prompt strictly bans generating available sizes, size charts, fiber percentages, price, or inventory.
- Output is enforced via strict JSON schema validation.

## 3. Resilience and Latency Bounding

- Bounded retries: Maximum 2 retries with exponential backoff on transient network timeouts.
- Non-retryable errors (e.g. policy violations, schema rejections) fail immediately.
- Comprehensive latency, token usage, and cost tracking recorded in `product_enrichment_model_runs`.
