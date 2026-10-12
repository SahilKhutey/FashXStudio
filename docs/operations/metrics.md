# Operations Metrics Tree & Data Definitions (Path B: Brand-First B2B)

**Governing Strategy**: Path B (B2B SaaS Fit Intelligence & Return Reduction Engine)  
**Reporting Standard**: Every metric is defined with mathematical precision, primary telemetry data source, functional owner, and Day 90 target.

---

## 1. North-Star Metric

### **Metric**: **Brands with a Live Widget & a Measured Return Reduction Result**
- **Exact Definition**: Count of unique active merchant tenants (`tenants.id` with `status = 'active'`) who have installed `fashx-widget.js` on their live production store and completed a pre/post return-rate delta audit across $\ge 500$ delivered orders on test SKUs.
- **Data Source**: `tenants` table joined with `tenant_usage` and audited return CSV reconciliation tables.
- **Owner**: Co-Founder & GTM Lead (joint with Technical Founder).
- **Target by Week 13**: **$\ge 3$ brands with audited results**.

---

## 2. Input Metrics Tree

```
                                  [NORTH STAR]
                     Brands with Live Widget & Measured Result
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
  [P1: Merchant Adoption]     [P2: Shopper Engagement]     [P3: Economic Impact]
  - Pilots Started            - Shopper Sessions / Brand   - Size Return Delta
  - Production Widgets Live   - Size Recs Delivered        - Paid Conversions
                              - Try-Ons Completed          - Gross Contribution
```

### Pillar 1: Merchant Acquisition & Onboarding
1. **Pilots Started (Pipeline)**:
   - *Definition*: Count of merchant tenants signing the 30-Day Measured Pilot Agreement and B2B DPA.
   - *Source*: CRM pipeline & signed contract repository.
   - *Owner*: GTM Co-Founder. Target by Week 13: **$\ge 6$ signed agreements**.
2. **Production Widgets Live**:
   - *Definition*: Count of distinct merchant domains pinging `/widget/v1/session` with active publishable keys in a 7-day rolling window.
   - *Source*: `tenant_keys` $\bowtie$ `widget_sessions` (`tenant_id`, `created_at >= now() - interval '7 days'`).
   - *Owner*: Technical Founder. Target by Week 13: **$\ge 3$ live stores**.

### Pillar 2: Shopper Interaction & Inference Volume
3. **Shopper Sessions per Brand**:
   - *Definition*: Count of unique anonymous shopper widget sessions initiated on product pages (`POST /widget/v1/session`).
   - *Source*: `widget_sessions` table (`count(id)` grouped by `tenant_id`).
   - *Owner*: Technical Founder. Target by Week 13: **$\ge 2,500$ sessions / brand / month**.
4. **Size Recommendations Delivered**:
   - *Definition*: Count of size advice cards viewed where chest/waist/hip mapping was successfully evaluated against the brand size chart.
   - *Source*: `tenant_usage.size_recs` column.
   - *Owner*: Technical Founder. Target by Week 13: **$\ge 1,800$ size recommendations / brand / month**.
5. **Visual Try-Ons Completed**:
   - *Definition*: Count of successful image diffusion inferences completed for shoppers in session (`status = 'completed'`).
   - *Source*: `tenant_usage.tryons` column.
   - *Owner*: Technical Founder. Target by Week 13: **$\ge 800$ try-ons / brand / month** (capped per tier).

### Pillar 3: Return Reduction & Revenue Realization
6. **Size-Related Return Rate on Tested SKUs**:
   - *Definition*: $\frac{\text{Returned Orders with Reason 'Size / Fit'}}{\text{Total Delivered Orders on Tested SKUs}} \times 100\%$.
   - *Source*: Shopify orders export & merchant return log CSV matched via `fashx_fit_token`.
   - *Owner*: GTM Co-Founder (joint audit with merchant COO).
   - *Target by Week 13*: **$\ge 3.0$ percentage point drop** vs. 60-day pre-pilot baseline.
7. **Paying Commercial Brands**:
   - *Definition*: Count of merchants with an active paid billing subscription ($\ge \text{₹15,000 / month}$).
   - *Source*: Bank receipts / Shopify App Billing API active subscriptions.
   - *Owner*: GTM Co-Founder. Target by Week 13: **$\ge 2$ paying brands**.
8. **Net B2B Gross Margin**:
   - *Definition*: $\frac{\text{Total SaaS Revenue} - \text{Total Compute Inference \& Infra Costs}}{\text{Total SaaS Revenue}} \times 100\%$.
   - *Source*: Monthly P&L ledger.
   - *Owner*: Both Founders. Target by Week 13: **$\ge 50.0\%$ Gross Margin**.
