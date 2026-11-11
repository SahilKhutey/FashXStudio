# FashXStudio — Phase 02.4: Mock & Fixture Inventory

**Document ID:** `FASHX-AUD-007`  
**Phase:** 02.4 — Audit Mock Versus Real Integrations (Execution C)  
**Date:** 2026-11-11  
**Author:** Antigravity Agent (Auditor)  
**Status:** COMPLETE (Audited Baseline)  
**Branch:** `recovery/rc13.1-governance-correction`  

---

## 1. Executive Summary

This inventory catalogues every mock implementation, fake response generator, test provider, seed fixture, simulated metric, and development storage path in the FashXStudio repository. It classifies each component by its actual operational role (Test-only, Development-only, Active Fallback, or Frozen Post-MVP).

---

## 2. Mock Class & Adapter Registry

| Class Name | File Location | Purpose & Behavior | Operational Role | Risk if Mistaken for Real |
|:---|:---|:---|:---:|:---:|
| `MockTryOnAdapter` | `backend/fashx/tryon/adapters/mock_adapter.py` | PIL-based compositing with red `PREVIEW ONLY - MOCK VTO` banner | Active Dev Default (`TRYON_PROVIDER=mock`) | **High** — Produces instant 2D image overlays, not generative diffusion try-on |
| `MockVlmClient` | `backend/fashx/catalog/enrichment/vlm.py` | Deterministic text-regex attribute extractor for titles & descriptions | Test & Offline Eval | **High** — Ignores image pixels; extracts attributes solely from keywords |
| `FakeEmbedder` | `backend/fashx/catalog/embeddings/fake.py` | Deterministic SHA-256 hashed 512-dim vectors; refuses non-dev `ENV` | Active Dev Default | **High** — Hash vectors have no semantic or visual representation |
| `TestPaymentProvider` | `backend/fashx/domain/payments/provider.py` | Generates dummy transaction IDs and simulated payment captures | Frozen Post-MVP (C09) | Low — Payment domain unmounted for external-checkout MVP |
| `TestCarrierProvider` | `backend/fashx/domain/fulfillment/carrier.py` | Generates dummy tracking numbers and simulated delivery labels | Frozen Post-MVP (C07) | Low — Carrier domain unmounted for external-checkout MVP |
| `InMemory*Repository` (26 classes) | `backend/fashx/repositories/*/memory.py` | Process memory data structures for cart, order, fulfillment, etc. | Core Bootstrap Registry / Frozen Domains | Medium — In-memory state does not persist across restarts |
| `InMemoryIdentityRepo` | `backend/fashx/security/identity.py` | In-memory user identity storage used in unit tests | Test-only | Low — Unit test fixture |

---

## 3. Seed Catalog & Hardcoded Fixture Data

The repository contains four structured seed catalogs:

| Data File Path | Size | Description & Origin | Permitted In Prod? |
|:---|:---:|:---|:---:|
| `data/catalog/curated-seed-catalog.csv` | 6.7 KB | Curated multi-brand apparel items with mock attributes | ❌ NO (ADR 0005) |
| `data/catalog/catalog_seed.csv` | 2.8 KB | Synthetic garments for initial schema seeding | ❌ NO (ADR 0005) |
| `data/catalog/sample-products.csv` | 621 B | Sample product records for unit test fixtures | ❌ NO (ADR 0005) |
| `data/partner-feed/products.csv` | 594 B | Mock partner merchant feed fixture | ❌ NO (ADR 0005) |

### Hardcoded Records in Scripts:
- **`scripts/catalog/sync_sources.py`:** Contains hardcoded sample item dictionaries for Amazon (`amazon_items`), Myntra (`myntra_items`), and Flipkart (`flipkart_items`) used to demonstrate multi-source ingestion.
- **`scripts/catalog/seed_local.py`:** Uses `FakeEmbedder` and hardcoded product URLs (`https://shop.example.com/products/...`).
- **Policy Compliance:** Under **ADR 0005** (`docs/adr/0005-catalog-sourcing.md`), all synthetic and seed catalogs must remain in `suspended` status. They are strictly prohibited from appearing in the live production discovery feed.

---

## 4. Simulated Fit Scores & Heuristics

| Component | Code Location | Nature of Score | Inputs Used |
|:---|:---|:---|:---|
| **B2B Widget Mock Endpoint** | `backend/fashx/b2b/widget.py:165` | **Hardcoded Simulated Constant** (`fit_score: 0.94`) | Static mock response for widget demo; disabled via `ENABLE_B2B=False` |
| **Discovery Scoring Candidate** | `backend/fashx/discovery/scoring.py:76` | **Default Constant** (`size_score = 1.0`) | Default score assigned when size chart comparison is absent |
| **Recommendation Compatibility** | `backend/fashx/recommendation/scoring.py` | **Rule-Based Heuristic** | Category compatibility rules, color harmony lookup, silhouette match |

**Finding:** FashXStudio currently does not use a 3D avatar or generative body-mesh predictor for fit scoring. Size and compatibility scores are rule-based heuristics. The B2B widget endpoint returns a simulated constant (`0.94`) and is intentionally disabled for the consumer MVP.

---

## 5. Development-Only Image & Storage Paths

1. **Local Filesystem Root:** `./.local_storage`  
   All uploaded user photos and mock VTO artifacts are written to `./.local_storage` when `STORAGE_BACKEND=local`.
2. **Development File Server Route:** `/dev-files/{file_path:path}`  
   Mounted in `backend/fashx/main.py:119` exclusively when `ENV in ("dev", "test")` to serve local images to the mobile client or browser.
3. **Signed URLs:** Generated by `LocalStorage.signed_get_url()`, returning `http://127.0.0.1:8000/dev-files/{key}?exp=...&sig=...`.
4. **Production Refusal:** `LocalStorage` raises a runtime exception if executed under `ENV=prod`.
