# RC13: Release Gates & Launch Governance (G1–G6)

## 1. Release Gates Definition
The six mandatory release gates governing public market launch:

| Gate | Title | Target Standard | Evaluator |
|---|---|---|---|
| **G1** | Automated Test & Build | Backend, mobile, and security test suites 100% green; zero unapproved skips. | CI Pipeline / pytest |
| **G2** | Database & Staging Services | PostgreSQL pgvector clean migration upgrade/downgrade/upgrade check. | `alembic upgrade head` |
| **G3** | Privacy & Quarantine Security | 0 PII leaks, 0 biometric data saved, 15-min signed URLs, account deletion verified. | [`scripts/rc13/validate_evidence.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/validate_evidence.py) |
| **G4** | Real Catalog Freshness | Active catalog with 0 broken links, valid visual embeddings, fresh inventory. | [`scripts/rc12/catalog_health.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/catalog_health.py) |
| **G5** | Real VTO Quality & Cost | Live GPU inference, completion >= 95%, defects <= 15%, P95 <= 30s. | [`scripts/rc13/evaluate_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_vto.py) |
| **G6** | Real User Pilot Validation | Real participant cohort (40–50 users), M1–M5 verified, 0 critical incidents. | [`scripts/rc13/evaluate_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_product_metrics.py) |

## 2. Gate Decision Engine
Implemented in [`scripts/rc13/evaluate_release_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_release_gates.py):
- **GO**: 6/6 gates PASS with authentic human evidence cards in `docs/evidence/` and documented reviewer signoff.
- **HOLD**: Any gate unmeasured, missing, or using synthetic/mock data. (Current status: HOLD).
- **FIX**: Any gate evaluated as FAIL.
