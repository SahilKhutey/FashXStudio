# Multi-Tier Global Budgets & Spend Safeguards

## 1. Budget Architecture

Virtual try-on operates under strict financial ceilings across three hierarchical tiers:

```
                            +--------------------------+
                            |     Platform Budget      |
                            |     ($500 / day default) |
                            +-------------+------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
       +-------------------------+                 +-------------------------+
       |    Merchant Budget      |                 |    Merchant Budget      |
       |    ($50 / day default)  |                 |    ($50 / day default)  |
       +------------+------------+                 +------------+------------+
                    |                                           |
             +------+------+                             +------+------+
             v             v                             v             v
       +-----------+ +-----------+                 +-----------+ +-----------+
       | Shopper 1 | | Shopper 2 |                 | Shopper 3 | | Shopper 4 |
       | ($5/day)  | | ($5/day)  |                 | ($5/day)  | | ($5/day)  |
       +-----------+ +-----------+                 +-----------+ +-----------+
```

### Scope Hierarchy:
1. **Platform Scope (`PLATFORM:GLOBAL`)**: Protects the company from catastrophic total spend in any single day or month.
2. **Merchant Scope (`MERCHANT:{merchant_id}`)**: Protects merchant accounts according to their tier or subscription.
3. **User Scope (`USER:{user_id}`)**: Prevents individual abusive accounts from consuming excessive GPU time.

---

## 2. Spend Allocation Table (`tryon_budgets`)

```sql
CREATE TABLE tryon_budgets (
    id UUID PRIMARY KEY,
    scope_type VARCHAR(32) NOT NULL,
    scope_id VARCHAR(128) NOT NULL,
    period VARCHAR(32) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    hard_limit_amount NUMERIC(12, 4) NOT NULL,
    warn_threshold_pct NUMERIC(5, 2) NOT NULL DEFAULT 70.00,
    crit_threshold_pct NUMERIC(5, 2) NOT NULL DEFAULT 90.00,
    current_spend_usd NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    reserved_spend_usd NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tryon_budgets_scope_period UNIQUE (scope_type, scope_id, period, period_start)
);
```

---

## 3. Thresholds and Actions

| Utilization Level | Threshold | Action |
|---|---|---|
| **Normal** | $< 70\%$ | Standard processing; routine metrics emitted. |
| **Warning** | $\ge 70\%$ | Emit CloudWatch warning alert; log Ops notification. |
| **Critical** | $\ge 90\%$ | Page on-call engineering; throttle non-essential background tasks. |
| **Exceeded** | $\ge 100\%$ | **Hard Stop**: Fail-closed gate. Reject new try-on inference with `BudgetExceededError`. |
