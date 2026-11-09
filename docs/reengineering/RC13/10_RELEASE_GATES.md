# RC13: Release Gates & Launch Governance (G1–G6)

## 1. Release Gates Matrix (Reconciled Standards)

| Gate | Title | Target Standard | Authenticated Verification Method |
|---|---|---|---|
| **G1** | Automated Test & Build | Backend, mobile, and security test suites 100% green; zero unapproved skips; clean CI run. | GitHub Actions CI Run log / `pytest` suite |
| **G2** | Database & Staging Services | PostgreSQL with `pgvector` extension; clean Alembic migration upgrade/downgrade/upgrade check. | `alembic upgrade head; downgrade -1; upgrade head` |
| **G3** | Privacy, Quarantine & Security | 0 PII leaks, 0 biometric identifiers persisted, 15-min signed URLs, S3 24h auto-purge, account erasure verified. | [`scripts/rc13/validate_evidence.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/validate_evidence.py) with `--verify-files` |
| **G4** | Real Catalog Freshness | Active catalog with verified merchant URLs, valid 512-dim visual embeddings, zero broken image assets (HTTP 200). | [`scripts/rc12/catalog_health.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/catalog_health.py) |
| **G5** | Real VTO Quality & Cost | Live commercial GPU provider; Completion $\ge 90.0\%$ (target $\ge 95\%$); Defect $\le 15.0\%$ (target $\le 10\%$); P95 $\le 45.0\text{s}$ (target $\le 30\text{s}$). | [`scripts/rc13/evaluate_vto.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_vto.py) |
| **G6** | Real User Pilot Validation | Controlled cohort (40–50 activated users); 12/12 Must-Haves (M1–M5) PASS; $\ge 3/4$ Should-Have groups PASS; 0 Stop Rules. | [`scripts/rc13/evaluate_product_metrics.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_product_metrics.py) |

---

## 2. Evidence Authentication Protocol

Evidence cards are strictly held to cryptographic and provenance standards:
1. **On-Disk Reference Verification**: The `source_file` path specified in the evidence record must exist on disk.
2. **SHA-256 Checksum Match**: The file's content must hash to the exact SHA-256 digest specified in the card.
3. **Authorized Human Reviewer**: Reviewer cannot be a placeholder (`unassigned`, `test`, `dummy`, `unknown`).
4. **Authentic Timestamp**: Must be a valid UTC ISO timestamp in the past or present.
5. **Zero Synthetic Tolerance**: Synthetic or mock records are rejected for production gate sign-offs.

---

## 3. Gate Decision Engine
Implemented in [`scripts/rc13/evaluate_release_gates.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc13/evaluate_release_gates.py):
- **GO**: 6/6 gates PASS with authentic human evidence cards in `docs/evidence/` and verified source files on disk.
- **HOLD**: Any gate unmeasured, missing, using synthetic data, or missing reviewer signoff. (Current baseline: `HOLD`).
- **FIX**: Any gate evaluated as `FAIL`.
