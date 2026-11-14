# FashXStudio — KPI Baseline Decision Log & Governance Record

**Document ID:** `FASHX-DEC-001`  
**Version:** `1.0 — Execution Baseline`  
**Date:** `10 November 2026`  
**Status:** `Approved Measurement Contract`  
**Scope:** `Phase 01.4 — Formal Metric Baseline Adoption`  

---

## 1. Formal Measurement Decisions Adopted

The following strategic decisions are formally locked as the measurement baseline for FashXStudio Pilot MVP v1.0:

| Decision ID | Metric / Area | Locked Strategic Decision | Rationale |
| :--- | :--- | :--- | :--- |
| **DEC-01** | VTO Reliability | VTO Job Success target locked at $\ge 90\%$. | Core technical viability threshold for user retention. |
| **DEC-02** | VTO Latency | Latency P95 ceiling locked at $< 45$ seconds. | Upper limit for acceptable mobile consumer waiting times. |
| **DEC-03** | Visual Quality | Realism and Garment Preservation both locked at $\ge 3.8 / 5.0$. | Minimum visual fidelity threshold required for consumer purchase confidence. |
| **DEC-04** | Commerce Boundary| Merchant outbound clicks define **Purchase Intent**, not completed sales. | Prevents false claims of revenue or return reduction without verified merchant conversion webhooks. |
| **DEC-05** | Unit Economics | Direct variable cost ($C_{\text{VTO}}$) target locked at $\le ₹12.00$ per try-on. | Required to ensure sustainable $\ge 65\%$ gross margins under merchant SaaS and usage pricing. |
| **DEC-06** | Telemetry Privacy | Zero raw biometric images or PII permitted in analytics events. | Enforces strict compliance with Indian DPDP Act 2023. |
| **DEC-07** | Merchant Reporting| Merchant Dashboard is classified **P1** for pilot; manual weekly export acceptable. | Prevents portal UI work from delaying core consumer try-on validation. |

---

## 2. Metric Modification Governance

Following the formal approval of Phase 1.4:
1. No KPI formula, denominator, or acceptance gate may be altered without filing a formal Change Request under [docs/product/MVP_CHANGELOG.md](file:///c:/Users/ASUS/Documents/FashXStudio/docs/product/MVP_CHANGELOG.md).
2. Targets cannot be lowered mid-pilot simply to convert a `FAIL` status into a `PASS`.
3. If an unforeseen technical limitation emerges (e.g. GPU provider baseline latency increases across the industry), a documented review with comparative external benchmarks must be logged.
