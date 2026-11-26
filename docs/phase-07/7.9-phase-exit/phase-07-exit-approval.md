# Phase 07 Exit Gate Acceptance Record

## 1. Release & Verification Metadata

| Acceptance Field | Recorded Audit Value |
| :--- | :--- |
| **Subsystem Release** | FashXStudio Virtual Try-On Subsystem (Phase 07) |
| **Git Commit SHA** | `5d46e4a` (Feature branch `feat/phase04.5-photo-upload`) |
| **Target Environment** | Staging / Pre-Production |
| **Configured Provider** | FASHN Commercial API (Adapter: `CommercialApiTryOnAdapter`) |
| **Model / Pipeline Version** | FASHN Model v1.5 / FashX Pipeline v1.0.0 |
| **Local / Sandbox Verification**| **260 Automated Tests Passed (100%)** |
| **Test Report Reference** | [`staging-test-report.md`](file:///docs/phase-07/7.9-phase-exit/staging-test-report.md) |
| **Quality Report Reference** | [`quality-report.md`](file:///docs/phase-07/7.9-phase-exit/quality-report.md) |
| **Evaluation Dataset Version**| `vto-eval-v1.0.0` (100 balanced image pairs) |
| **Security Review** | Completed by Engineering Agent (2026-11-25) |
| **Cost & Quota Ledger** | Verified in `tests/unit/tryon/cache/run_all_cost_control_tests.py` |
| **Known Limitations** | Documented in [`known-limitations.md`](file:///docs/phase-07/7.9-phase-exit/known-limitations.md) |
| **Final Exit Decision** | 🟡 **CONDITIONAL ACCEPTANCE** (Code Complete & Sandbox Verified; Pending Founder Staging Egress Run) |

---

## 2. Gate Verification Summary (Gates A through F)

- **Gate A — Real Inference**: Provider adapter, secret configuration, request fingerprinting, output sanitization, and cost logging implemented and verified in sandbox. Bounded live execution against external FASHN servers requires founder production credentials.
- **Gate B — Security & Privacy**: 🟢 **PASSED**. Shopper image ownership, runtime consent check (Time-of-Use guard), private S3 buckets, presigned URLs (TTL 15m), and BOLA denial verified.
- **Gate C — Reliability**: 🟢 **PASSED**. 18-state transition machine enforced, idempotency verified, duplicate queue delivery handled, worker lease recovery verified, DLQ active.
- **Gate D — Cost Controls**: 🟢 **PASSED**. User rate limits (5 req/10m), user daily quotas (20/day), merchant budget limits, and global kill switch verified.
- **Gate E — Quality**: 🟢 **PASSED**. `vto-eval-v1.0.0` dataset manifest accepted. Category gates approved for casual shirts, t-shirts, kurtas, trousers, and jeans. Unsupported categories (sarees, lehengas, footwear) fail closed.
- **Gate F — Shopper Experience**: 🟢 **PASSED**. Mandatory visual try-on disclosure (`VISUAL_TRYON_NOT_FIT_VERIFICATION`), prohibition of fit guarantees, separate merchant size charts, and shopper reporting with 9 reason codes verified.

---

## 3. Outstanding Actions for Full Production Release

In accordance with repository engineering rules (AGENTS.md):
1. **GitHub Actions CI Run**: Automated local gate and PostgreSQL migration upgrade (`alembic upgrade head`) will run in CI with configured PostgreSQL service.
2. **Founder Staging Live Run**: The human founder will trigger a bounded staging test (`max_requests: 1`) using the production FASHN API key to generate the live provider request ID and external invoice reconciliation evidence.
3. **Evidence Card**: Only the human founder creates the final real-world evidence card in `docs/evidence/`.
