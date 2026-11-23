# Phase 05.7 — Catalog Quality and Target Dashboard Specification

## 1. Overview
The Catalog Quality Dashboard provides administrative visibility into pilot catalog targets, automated quality measurements, source compliance, link availability, and release gate readiness.

---

## 2. API Endpoints Specification

All metrics and evaluation endpoints are located under prefix `/api/v1/admin/catalog` and enforce mandatory administrative authentication (`require_role("admin")`).

### 2.1 Endpoints Summary Table

| Method | Endpoint | Description | Response Model / Schema |
|:---|:---|:---|:---|
| `GET` | `/admin/catalog/targets` | Get current versioned pilot target definitions and thresholds | `TargetConfig` |
| `POST` | `/admin/catalog/evaluations` | Execute on-demand catalog evaluation across all 7 targets | `EvaluationReport` (HTTP 201) |
| `GET` | `/admin/catalog/evaluations/{id}` | Get summary and release decision for a specific evaluation | `dict` (Status, summary metrics) |
| `GET` | `/admin/catalog/evaluations/{id}/report` | Get complete detailed audit report with breakdown | `dict` (Full immutable run report) |
| `GET` | `/admin/catalog/metrics` | Retrieve latest metric snapshot across all 7 targets | `dict[str, CatalogMetricResult]` |
| `GET` | `/admin/catalog/source-health` | Source authorization and live feed health breakdown | `dict` (Live feeds, unauthorized sources) |
| `GET` | `/admin/catalog/quality` | Usable products breakdown and rejection counts | `UsableProductCheckResult` |
| `GET` | `/admin/catalog/price-freshness` | Sampled price freshness metrics and stale counts | `dict` (Metric + freshness details) |
| `GET` | `/admin/catalog/link-health` | Sampled destination link health and SSRF check results | `dict` (Metric + broken counts) |
| `GET` | `/admin/catalog/image-compliance` | Image permission traceability and operational rights matrix | `dict` (Metric + rights breakdown) |

---

## 3. UI Dashboard Layout & Components

### 3.1 Primary Status Bar (Release Gate Verdict)
- **Status Indicator:** `ACCEPT` (Green) or `HOLD` (Amber/Red).
- **Active Blockers List:** Displaying specific failures (e.g., `"Source Compliance Blocker: 1 unauthorized source"`, `"Usable Catalog Blocker: 412 offers (< 1000)"`).
- **Trigger Evaluation Button:** Allows platform administrators to trigger a new evaluation run with custom sample sizes or seeds.

### 3.2 Target Metric Cards (7 Grid Cards)
1. **Live Authorized Feeds:** Active count vs Target ($\ge 1$). Shows qualified adapter names and verified merchant IDs.
2. **Usable Products:** Usable offers count vs Target ($\ge 1,000$). Displays canonical garment and variant sub-counts.
3. **Expansion Band:** Volume vs 2,000–5,000 band. Flagged as `CONDITIONAL`.
4. **Price Freshness:** Percentage fresh vs Target ($\ge 95.0\%$). Shows counts of fresh, stale, and unverified prices.
5. **Broken Product Links:** Percentage broken vs Target ($< 1.0\%$). Shows breakdown by HTTP 404, 410, and SSRF blocks.
6. **Unauthorized Sources:** Count of unverified sources vs Target ($0$). Zero-tolerance compliance banner.
7. **Image Traceability:** Traceable percentage vs Target ($100.0\%$). Displays operational rights breakdown (display, store, VTO).

---

## 4. Security & Access Control
1. **Default-Deny:** Unauthenticated requests receive HTTP 401.
2. **Role Restriction:** Non-admin roles (including `merchant_operator` and public shoppers) receive HTTP 403 Forbidden.
3. **Secret Redaction:** Evaluation reports never output sensitive credential strings, passwords, or vault secret references.
