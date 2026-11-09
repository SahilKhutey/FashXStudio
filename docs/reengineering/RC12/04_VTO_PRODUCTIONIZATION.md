# RC12: Virtual Try-On Productionization and Cost Accounting

## 1. Objectives
Ensure try-on operations maintain honest provenance labeling, strict user quotas, spend budget alerts, job idempotency, and predictable queue SLAs.

## 2. Provenance Contract & Result Modes
Every try-on output is assigned an explicit execution mode:
- `mode: "real"`: Live vendor GPU inference with recorded `provider`, `model_version`, `duration_ms`, and `cost_usd`.
- `mode: "mock"`: Synthetic preview; provider and cost fields remain explicitly null/unknown.
- `mode: "cached"`: Previously computed output for identical input hashes; labeled as cached.
- `mode: "failed"`: Terminated or timed-out job with safe error category.

## 3. Cost & Spend Accounting
Monitored via [`scripts/rc12/vto_cost_report.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc12/vto_cost_report.py):
- **Spend Warning Threshold**: Triggered when cumulative spend reaches $\ge 80\%$ of budget ($\ge \$280 / \$350$).
- **Per-User Quotas**: Enforced server-side to prevent malicious exhaustion of API credits.
- **Job Idempotency**: Duplicate job submissions with identical user/garment hashes return the existing active job ID.
