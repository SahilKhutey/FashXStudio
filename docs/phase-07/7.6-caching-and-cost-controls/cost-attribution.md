# Cost Attribution & Cache ROI Analysis

## 1. Unit Economics Formulation

The platform tracks two critical financial dimensions:
1. **Realized Spend**: What was paid to third-party inference providers.
2. **Cache Savings**: What would have been spent if cached requests had required fresh provider inference.

### 1.1 Realized Cost Per Job
$$\text{Cost Per Successful Job} = \frac{\sum \text{TryOnProviderUsage.total\_cost\_usd}}{\text{Count of Successful Jobs}}$$

Because jobs can undergo retries, this metric captures total cost including retries, polling, and ambiguous attempt overheads.

### 1.2 Estimated Cache Savings
$$\text{Cache Savings (USD)} = \sum_{\text{cache hits}} \Big(\text{Unit Cost of Provider/Model}\Big)$$

For instance, 10,000 cache hits on FASHN standard quality ($0.075 / call) yields:
$$10,000 \times \$0.075 = \$750.00 \text{ saved}$$

---

## 2. Telemetry and Analytics Pipeline

```
     +--------------------------+
     |   tryon_provider_usage   |
     |   (realized spend)       |
     +------------+-------------+
                  |
                  +--------------------------------+
                  |                                |
                  v                                v
     +--------------------------+    +--------------------------+
     |   tryon_result_cache     |    |   CloudWatch / Grafana   |
     |   (hit_count, savings)   |    |   Cost Dashboard         |
     +--------------------------+    +--------------------------+
```

The `TryOnCostService.get_period_cost_summary(from_time, to_time)` aggregates:
- `total_spend_usd`: Exact dollars debited from ledger.
- `total_operations`: Raw count of API calls made.
- `successful_jobs`: Number of completed VTO user experiences delivered.
- `cost_per_successful_job_usd`: Effective unit acquisition cost.
- `cache_hits`: Number of shopper requests fulfilled via cache.
- `estimated_cache_savings_usd`: Net dollar value preserved.
