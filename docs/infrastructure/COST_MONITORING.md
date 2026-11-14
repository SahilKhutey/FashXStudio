# Cost Monitoring & Financial Governance

## 1. Overview

FashXStudio enforces proactive cost monitoring across both AWS cloud infrastructure and third-party AI model inference providers.

Cost management operates at three distinct layers:
1. **AWS Budgets & Anomaly Detection**: Monthly financial ceilings with multi-tiered notification thresholds.
2. **Telemetry Cost Governance**: Strict metric cardinality controls and log retention policies to prevent runaway CloudWatch fees.
3. **Third-Party Inference Tracking**: Per-render cost accounting for Virtual Try-On API providers.

## 2. AWS Budgets Configuration

Budgets are declared in `infra/aws/observability/budgets/budgets.yaml` across environments:

| Budget Name | Environment | Monthly Limit (USD) | Alert Thresholds | Notification Target |
| :--- | :--- | :--- | :--- | :--- |
| `fashx-monthly-dev-budget` | `dev` | $100.00 | 50% (actual), 80% (actual), 100% (actual) | Engineering Lead |
| `fashx-monthly-staging-budget` | `staging` | $250.00 | 50% (actual), 80% (actual), 100% (actual) | Engineering Lead |
| `fashx-monthly-prod-budget` | `prod` | $750.00 | 50% (actual), 80% (actual), 100% (forecasted) | Founder / Operations |
| `fashx-monthly-total-budget` | All Accounts | $1,200.00 | 70% (actual), 90% (actual), 100% (forecasted) | Founder / On-Call |

### Alert Actions
- **50% Actual Spend**: Informational email; confirms that spend trajectory matches planned usage.
- **80% Actual Spend**: Operational review of idle ECS tasks, orphaned EBS volumes, and stale staging containers.
- **100% Forecasted Spend**: Triggered when the current burn rate projects month-end budget breach; triggers immediate review of scale factors.

## 3. Telemetry & Custom Metric Cost Controls

AWS CloudWatch custom metrics incur costs per unique metric dimension combination ($0.30 per metric/month for the first 10,000 metrics). High-cardinality values placed into metric dimensions can generate tens of thousands of metric combinations and result in unexpected costs.

### Cardinality Enforcement
The metric emitter (`backend/fashx/core/metrics.py`) strips prohibited dimensions:
- Never use `user_id`, `request_id`, `trace_id`, or `job_id` in dimensions.
- Use route templates (`/api/v1/tryon/{job_id}`) rather than concrete paths (`/api/v1/tryon/12345`).
- Total active custom metric series across all FashX namespaces is capped under 150 combinations.

### Log Retention Policies
To minimize log storage and indexing fees, retention is configured strictly in `infra/aws/observability/cloudwatch/log-groups.yaml`:
- **Development**: 7 days retention.
- **Staging**: 14 days retention.
- **Production**: 30 days retention (with optional export to S3 Glacier for long-term audit compliance).

## 4. Upstream AI / VTO Inference Cost Accounting

Virtual Try-On models (such as FASHN API) incur per-call inference charges.
- The FASHN adapter (`backend/fashx/infrastructure/tryon/fashn_api.py`) emits `VTOProviderCostEstimate` upon every successful generation.
- Operators track cumulative spend via CloudWatch Metric Math:
  ```text
  SUM(METRICS("FashX/VTO", "VTOProviderCostEstimate", "Environment", "prod"))
  ```
- This metric provides real-time unit economics visibility per completed try-on transaction.
