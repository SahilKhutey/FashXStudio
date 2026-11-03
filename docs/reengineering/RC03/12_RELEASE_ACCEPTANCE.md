# RC-03 — Release Acceptance Scorecard

## Acceptance Criteria & Status

| ID | Criteria | Required Output | Verified State |
|---|---|---|---|
| **AC-01** | User identity & query isolation | Distinct cache keys per `userId`; cache cleared on signout | 🟢 Verified (`queryKeys.test.ts`) |
| **AC-02** | Safe shopping redirects | Strict HTTPS & approved host filtering | 🟢 Verified (`safeRedirect.test.ts`) |
| **AC-03** | Discovery feed loading | 20 cleared catalog products with stylist explanations | 🟢 Verified (`scripts/rc03_smoke.py`) |
| **AC-04** | Outbound commerce handoff | Attribution tracking & signed redirect URL generated | 🟢 Verified (`scripts/rc03_smoke.py`) |
| **AC-05** | Wardrobe persistence | Save, query, and remove lifecycle operational | 🟢 Verified (`scripts/rc03_smoke.py`) |
| **AC-06** | System health probes | `/healthz/live` & `/healthz/ready` return 200 | 🟢 Verified (`scripts/rc03_smoke.py`) |
| **AC-07** | Automated test suite | Mobile Jest & Backend Pytest suites green | 🟢 Verified (152 Jest, 907 Pytest) |
| **AC-08** | TypeScript integrity | `tsc --noEmit` exits with 0 errors | 🟢 Verified (`npm run typecheck`) |
| **AC-09** | OpenAPI documentation | Snapshot exported to `artifacts/rc03/openapi.json` | 🟢 Verified (844 KB) |

> [!NOTE]
> Per AGENTS.md rules, rows are marked 🟢 based on verified command outputs from code and CI execution. Human evidence cards (✅) remain strictly reserved for the human founder.
