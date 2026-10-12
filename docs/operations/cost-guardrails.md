# Infrastructure Cost Guardrails & Unit Economics Controls

- **Version:** 1.0 (Phase 12 Operating Foundation)
- **Currency:** Indian Rupee (INR / ₹)
- **Target Unit Margin:** $\ge 65\%$ Gross Margin on B2B SaaS Subscriptions

---

## 1. Unit Cost Ceilings (Cost per Unit of Work)

To ensure sustainable unit economics across all merchant tiers, the platform enforces strict marginal cost ceilings:

| Operation | Target Cost | Hard Ceiling | Optimization Mechanism |
|---|---|---|---|
| **Virtual Try-On Inference** | $\le ₹1.15$ | $₹1.50$ | Spot GPU instances, 8-bit quantized weights, adaptive resolution |
| **Widget Asset Delivery (1k views)** | $\le ₹0.04$ | $₹0.08$ | Cloudflare Edge caching, Brotli compression ($< 45\text{KB}$) |
| **Storage per Session (24h ephemeral)** | $\le ₹0.005$ | $₹0.01$ | Automated S3 lifecycle rules (24h instant expiration) |
| **Database Transaction per Session** | $\le ₹0.002$ | $₹0.005$ | Read replicas, Redis connection pooling, batched event writes |
| **Blended Marginal Cost per Try-On** | $\mathbf{\le ₹1.20}$ | $\mathbf{\le ₹1.60}$ | Real-time billing guardrails and queue throttling |

---

## 2. Monthly Spend Ceilings & Alerts

The Phase 12 90-day execution budget is capped at **₹1,25,000 / month** across all cloud infrastructure:

| Infrastructure Category | Monthly Budget Cap | Alerts Threshold |
|---|---|---|
| **GPU Inference Pool (RunPod / AWS Spot)** | ₹75,000 | 75% at ₹56,250 / 90% at ₹67,500 |
| **Application & DB Cluster (AWS ECS + RDS)** | ₹30,000 | 80% at ₹24,000 |
| **CDN & Storage (Cloudflare + S3)** | ₹10,000 | 80% at ₹8,000 |
| **Monitoring & Observability (Datadog/Sentry)** | ₹10,000 | 80% at ₹8,000 |
| **Total Cloud Ceiling** | **₹1,25,000** | Daily spend rate $> ₹4,200$ |

### Automated Guardrails & Circuit Breakers
1. **Idle GPU Kill-Switch:** Workers scale to zero when queue depth is 0 for $> 10$ consecutive minutes.
2. **Anomaly Alerting:** If daily inference spend exceeds $1.5\times$ 7-day moving average, notify `#ops-cost` on Slack.
3. **Emergency Circuit Breaker:** If total monthly spend hits 100% of cap before the 25th of the month, non-enterprise free-tier generations are throttled to low-priority spot compute.

---

## 3. Merchant Subscription Tiers & Quota Controls

| Plan Tier | Monthly Fee | Included Try-Ons | Marginal Value per Try-On | Overage Rate |
|---|---|---|---|---|
| **Design Partner (Pilot)** | ₹15,000 | 3,000 | ₹5.00 | ₹2.50 / try-on |
| **Growth B2B** | ₹25,000 | 7,500 | ₹3.33 | ₹2.25 / try-on |
| **Scale Enterprise** | Custom (₹60,000+) | 25,000+ | ₹2.40 | ₹1.80 / try-on |

- **Gross Margin Protection:** At ₹15,000 for 3,000 try-ons, compute cost is $3,000 \times ₹1.20 = ₹3,600$. Gross margin is:
  $$\frac{₹15,000 - ₹3,600}{₹15,000} = 76.0\%$$
  This satisfies the pre-committed target of $\ge 65\%$ gross margin.
