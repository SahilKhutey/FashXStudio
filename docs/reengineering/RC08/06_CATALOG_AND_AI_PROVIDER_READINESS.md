# RC08 — Catalog & AI Provider Readiness

## 1. Catalog Rights & Source Authorization
FashX strictly operates on authorized fashion catalog data:
- **Direct Clearance Required**: `CatalogSource` status must be `"cleared"`, with `rights_display=True` and `rights_tryon=True`.
- **Image Policy**: `mirror` (safe internal copy with ownership attribution) or `direct` (licensed CDN URL).
- **Price Freshness**: Ingestion timestamps are maintained; offers older than 72 hours trigger a freshness flag in the mobile UI.

## 2. Multimodal Embedding Provider Status
- **Development/Test Provider**: `mock-fake-512:mock-v1` generates deterministic hash-based 512-dimensional vectors. It is strictly forbidden in production.
- **Production Model**: `Marqo/marqo-fashionCLIP:2026.1` generates real 512-dimensional multimodal vision-language embeddings.
- **Reconciliation Rule**: Documentation must clearly distinguish between test-mock embeddings and live FashionCLIP inference. No claim of real embedding inference can be made without real inference execution logs.

## 3. Virtual Try-On (VTO) Provider Execution
- **Vendor**: Fashn.ai API (`tryon-v1.6`).
- **Cost & Rate Control**:
  - `tryon_user_daily_cap`: 20 requests/user/day.
  - `tryon_daily_budget_usd`: $20.00 hard cap.
  - Fail-closed behavior: If budget is reached or vendor returns 429/500, user receives a clean, non-crashing service message.
- **Truthful Output Guarantee**: Mock try-on results must never be disguised or passed off to users as genuine AI-generated images.
