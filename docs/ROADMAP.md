# FashXStudio: Program Master Roadmap (Phases 0 – 13)

- **Product:** FashXStudio — AI Personal Stylist & Virtual Try-On Platform (Merchant-First B2B2C Discovery)
- **Current Lifecycle Stage:** **Pre-Pilot Engineering Foundation & Validation** (Master Blueprint Phase 01–02)
- **Last Updated:** 2026-11-11
- **Current Branch:** `recovery/rc13.1-governance-correction`
- **Release Status:** **HOLD** (Software gates implemented; real-world commercial evidence unmeasured per [docs/provenance.md](provenance.md))

---

## 1. Governance & Dual-Track Evaluation Model

To prevent rehearsal scenarios and synthetic benchmarks from being mistaken for achieved market traction, this roadmap tracks progress along two strictly independent dimensions:

1. **Engineering Implementation:** Architecture, repository code, swappable adapters, unit/integration tests, and CI automation.
2. **Real-World Evidence:** Real users, executed merchant agreements, live cloud infrastructure, paid vendor inference, and authentic commercial transactions.

---

## 2. Program Trajectory & Historical Milestones

```
Phase 0: Baseline & Repository Audit (Oct 2026) ────────────────────────── [Tag: v0.0-baseline]
  ↳ Ground-truth audit of dependencies, licenses, mock code, and technical debt

Phase 1: Honest Documentation & Restructure (Oct 2026) ─────────────────── [Tag: v0.1-docs]
  ↳ Single source of truth, quarantine of simulated rehearsal figures to docs/_simulated/

Phase 2: Codebase Unification & Package Hygiene (Oct 2026) ─────────────── [Tag: v0.2-unified]
  ↳ Elimination of duplicate app roots; canonical backend/fashx package

Phase 3: Security & Auth Spine (Oct 2026) ──────────────────────────────── [Tag: v0.3-auth]
  ↳ Default-deny API gateway, JWT verification, tenant/user ownership scopes

Phase 4: Persistence, Database & S3 Storage (Oct 2026) ─────────────────── [Tag: v0.4-persistence]
  ↳ PostgreSQL + pgvector schemas, Alembic migrations, S3 adapter (live cloud unverified)

Phase 5: Virtual Try-On Pipeline & Abstraction (Oct 2026) ──────────────── [Tag: v0.5-tryon]
  ↳ FASHN API adapter implemented; Mock adapter default; paid inference unverified

Phase 6: Catalog Ingestion & Normalization (Oct 2026) ─────────────────── [Tag: v0.6-catalog]
  ↳ Google Merchant XML/CSV parsers, dHash deduplication; live merchant feed unverified

Phase 7: Discovery Feed & Personalization (Oct 2026) ───────────────────── [Tag: v0.7-discovery]
  ↳ 11-feature vector scoring, MMR diversity ranking; human relevance ratings unverified

Phase 8: Mobile Client — React Native / Expo (Oct 2026) ────────────────── [Tag: v0.8-mobile-mvp]
  ↳ Expo SDK 57 iOS/Android app, Jest test suite (165 tests); physical hardware pending

Phase 9: Privacy Hardening & Governance Framework (Oct 2026) ───────────── [Tag: v0.9-pilot-ready]
  ↳ DPDP cascading erasure, fail-closed release gate engine; external legal sign-off unverified

Phase 10: Closed Pilot Framework & Rehearsal (Oct 2026) ────────────────── [Tag: v0.10-pilot-complete]
  ↳ Pre-registered pilot plan; 38-user metric rehearsal (quarantined simulated scenario)

Phase 11: Strategic Evaluation & Architecture Selection (Oct 2026) ─────── [Tag: v1.0-decision]
  ↳ Scorecard decision modeling (Path B B2B2C discovery handoff); commercial traction unverified

Phase 12: Operating Foundation & Governance Consolidation (Oct–Nov 2026) ─ [Tag: v1.1-gate2]
  ↳ Productization code, multi-tenant widget; Gate 2 scale claims quarantined as rehearsal

Phase 13: Commercial Scale-Out & Live Pilot Deployment (Future Workstream)─ [PLANNING TARGETS]
  ↳ Live merchant pilot, commercial FASHN key activation, S3 cloud deployment, seed fundraising
```

---

## 3. Phase-by-Phase Status & Evidence Reconciliation

| Phase | Core Objective | Engineering Implementation Status | Real-World Evidence Status | Status Classification |
|:---|:---|:---|:---|:---:|
| **Phase 0** | Codebase Audit | Repository audit, dependency lockfiles | Verified in repository | `VERIFIED_ENGINEERING` |
| **Phase 1** | Docs Restructure | Honest STATUS.md, architecture ADRs | Clean documentation baseline | `VERIFIED_ENGINEERING` |
| **Phase 2** | Code Hygiene | Canonical `backend/fashx/` package | 1,058 unit tests passing | `VERIFIED_ENGINEERING` |
| **Phase 3** | Auth Spine | Gateway, local JWT verifier, RBAC | Local auth verified; external JWKS unverified | `LOCAL` |
| **Phase 4** | Real Storage | PostgreSQL models, Alembic migrations, S3 adapter | CI container verified; live cloud unverified | `LOCAL` |
| **Phase 5** | Try-On Engine | FASHN adapter, Mock adapter, watermark, quality gate | Mock default verified; real API inference unverified | `LOCAL` |
| **Phase 6** | Real Catalog | CSV/XML parsers, dHash deduplication, source registry | Local fixtures verified; live partner feed unverified | `LOCAL` |
| **Phase 7** | Discovery Feed | Constrained MMR ranker, 11-feature scoring | Synthetic personas verified; human ratings unverified | `LOCAL` |
| **Phase 8** | Mobile MVP | Expo SDK 57 app, 22 Jest suites (165 tests) | CI/simulator verified; physical device pending | `LOCAL` |
| **Phase 9** | Hardening & DPDP | Cascading erasure use case, release gate evaluators | Code verified; outside legal counsel unverified | `LOCAL` |
| **Phase 10** | Closed Pilot | Pre-registered pilot plan, metric calculation scripts | Simulated rehearsal in `_simulated/`; live pilot not run | `SIMULATED` |
| **Phase 11** | Strategy & Decision | 5-way decision model, B2B2C handoff ADR (ADR-0009) | Strategic analysis complete; market traction unverified | `PLANNING_TARGET` |
| **Phase 12** | 90-Day Productization | Multi-tenant widget backend, release gate evaluator | Code verified; Gate 2 scale metrics quarantined | `SIMULATED` |
| **Phase 13** | Commercial Scale | Scale-out planning, infrastructure architecture | Future targets; zero commercial revenue achieved | `PLANNING_TARGET` |

---

## 4. Phase 13 Workstreams: Future Planning Targets & Assumptions

*Note: The items below represent directional hypotheses and engineering plans. They are not completed achievements.*

### Pillar 1: Self-Serve Product & Merchant Integrations
- **Live Merchant Pilot (P0):** Onboard 1–3 real Indian fashion brands with documented metadata, image display, and AI try-on rights (ADR 0005).
- **Merchant Storefront Widget:** Shadow DOM `<45KB` embeddable try-on widget with external merchant checkout handoff (ADR 0009).
- **Automated Catalog Ingestion:** Automated daily sync via scheduled GitHub Actions / Celery workers.

### Pillar 2: Scalable Compute & Infrastructure Hardening
- **Production AI Inference (P0):** Activate commercial FASHN API key with budget ceiling enforcement ($20.00/day).
- **Cloud Media Storage (P0):** Deploy S3/Cloudflare R2 bucket with automated artifact retention (48-hour guest TTL).
- **Managed Database (P0):** Managed PostgreSQL 16 instance with `pgvector` extension and automated backups.

### Pillar 3: Capital & Commercial Growth Hypotheses
- **Seed Fundraising Planning:** Institutional seed round target (₹3.5–5.0 Cr) conditional on authentic Pilot MVP validation.
- **Grant Applications:** Startup India Seed Fund Scheme (SISFS) non-dilutive grant tracking.
- **Target Commercial Capacity:** 50 live partner brands, ₹12,00,000 monthly recurring revenue ($1.44 Cr ARR target hypothesis).
