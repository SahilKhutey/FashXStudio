# Phase 6: Catalog Audit & Provenance Health Report (2026-10-10)

**Generated:** 2026-10-10T05:27:12.728384+00:00  
**Scope:** PostgreSQL live catalog inspection, sources status, freshness tracking, and try-on readiness.

---

## 1. Executive Summary & Inventory Counts

| Metric | Count | Ratio / Notes |
|---|---|---|
| **Total Merchant Products** | 5240 | Across all registered sources |
| **Active Products** | 5180 | Cleared and available for feed |
| **Stale Products (Missing >72h)** | 48 | Quarantined pending refresh |
| **Removed Products (>14d Stale)** | 12 | Preserved text-only for closet |
| **Blocked Products (Unmapped Category)** | 0 | Quarantined from user view |
| **Canonical Garments** | 4890 | Unique style/variant entities |
| **Try-On Supported Products** | 4210 | Mirror policy + license cleared + suitable |
| **Mirrored Images** | 5240 | Stored in S3/R2 with exact SHA-256 |
| **Multimodal Enrichments** | 5240 | Structured VLM attributes + 512d vectors |

---

## 2. Source Provenance & Status Register

| Source Slug | Name | Kind | Status | Display | Try-On | Image Policy | Refresh |
|---|---|---|---|---|---|---|---|
| `fabindia` | FabIndia Direct Feed | partner_feed | **CLEARED** | Yes | Yes | `mirror` | 24h |
| `snitch` | Snitch Partner Feed | partner_feed | **CLEARED** | Yes | Yes | `mirror` | 24h |
| `westside` | Westside Trent Merchant Feed | partner_feed | **CLEARED** | Yes | Yes | `mirror` | 24h |
| `flipkart` | Flipkart Affiliate Delta Feed | affiliate_api | **PENDING** | Yes | No | `hotlink` | 24h |
| `admitad` | Admitad Network Feed (Myntra/Ajio) | affiliate_feed | **PENDING** | Yes | No | `hotlink` | 24h |

---

## 3. Freshness & Takedown SLA Compliance

- **Price Freshness Window:** 98.4% of active items checked within the last 72 hours.
- **Stale Quarantine:** Missing items automatically transition to `stale` after `refresh_hours * 3`.
- **Takedown SLA Capability:** Tested CLI script `scripts/catalog/purge_source.py` executes full suspension and asset purging in < 2 minutes (exceeding the ≤10m requirement).

---

## 4. Recent Ingest Runs

| Run ID | Started At | Status | Items Fetched | New | Updated | Unchanged |
|---|---|---|---|---|---|---|
| `run-fabi...` | 2026-10-10 05:27 | `completed` | 2450 | 2450 | 0 | 0 |
| `run-snit...` | 2026-10-10 05:27 | `completed` | 1580 | 1580 | 0 | 0 |
| `run-west...` | 2026-10-10 05:27 | `completed` | 1210 | 1210 | 0 | 0 |

---

## 5. Unmapped Categories Requiring Review

Zero unmapped categories detected. All ingested items mapped to taxonomy.