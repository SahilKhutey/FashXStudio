# Pilot Unit Economics & Commercial Viability Model (ROUGH ESTIMATE)

> [!NOTE]
> **Status & Disclaimer**: This financial model represents a preliminary, rough estimation based on closed pilot operational telemetry (Phase 10). Affiliate network conversions take 30–60 days to reconcile post-validation, and transaction data is limited to initial pilot click-outs. All conversion rates and affiliate commissions are explicitly identified as parameterized assumptions with sensitivity ranges.

---

## 1. Operational Cost Structure (Per Active User)

Based on real production expenditures observed during the 4-week closed pilot with 38 active users handling 215 AI try-on generations:

### A. Monthly Fixed & Shared Infrastructure
- Cloud Compute (FastAPI API server + Redis instance + PostgreSQL RDS): **$65.00 / month**
- Object Storage (S3 ephemeral staging & watermarked assets): **$8.50 / month**
- Auth & Base Email Services (Supabase Pro baseline): **$25.00 / month**
- **Total Shared Infrastructure**: **$98.50 / month**
- *Infrastructure Cost per Active User (at pilot scale n=38)*: **$2.59 / user / month** ($0.65 / user / week)
- *Projected Infrastructure Cost at 2,000 MAU*: **~$0.12 / user / month** ($0.03 / user / week due to economies of scale)

### B. Variable Marginal Costs (Per User per Week)
- **AI Try-On Inference**:
  - Observed median try-on jobs per user per week: **1.35 jobs / week**
  - Cost per inference call (GPU spot / vendor volume pricing): **$0.065 / generation**
  - Cost per user per week: **$0.088 / week** (~₹7.30 / week)
- **Catalog Ingestion & Vector Indexing**:
  - Continuous catalog enrichment, embedding generation & delta sync: **$0.015 / user / week**
- **Transactional Messaging / Verification**:
  - Session security & notifications: **$0.005 / user / week**
- **Total Variable Cost per Active User**: **$0.108 / user / week** (~₹9.00 / week)

### Total Operational Cost per Active User
$$\text{Total Cost / Active User / Week} = \$0.65 \text{ (Infra at pilot scale)} + \$0.11 \text{ (Variable)} = \mathbf{\$0.76 \text{ / week}} \ (\approx \text{₹63 / week})$$
*(At target commercial scale of 2,000+ MAU, infrastructure amortizes to $0.03/week, yielding a steady-state cost of **$0.14 / active user / week** or ~₹11.60 / week).*

---

## 2. Monetization & Revenue Assumptions (Affiliate Commerce Model)

Monetization is driven by performance-based affiliate commissions when users click "Buy on Store" to partner merchants (Myntra, Ajio, Tata CLiQ) using tracked affiliate sub-IDs (`sub_id=fx_user_garment`).

### Key Revenue Parameters & Assumptions:
1. **Average Order Value (AOV)**:
   - Baseline assumption: **₹1,850 INR** (~$22.30 USD) based on current ingested catalog price points for kurtas, dresses, and shirts.
2. **Affiliate Commission Rate**:
   - Fashion apparel commission rates on Indian affiliate networks (Impact, Cuelinks, EarnKaro):
     - Western Fashion: **8.0%**
     - Ethnic Wear: **7.5%**
     - Blended Weighted Average Commission: **7.8%** (~₹144.30 INR or $1.74 USD per validated transaction).
3. **Weekly Outbound Buy Clicks**:
   - Pilot observed performance: 18 users generated 34 outbound buy clicks over 4 weeks $\rightarrow$ **0.22 buy clicks / active user / week**.

---

## 3. Revenue Sensitivity & Break-Even Analysis

Because affiliate sales validate over 30–60 days, we model three scenarios for the Click-to-Purchase Conversion Rate ($\text{CR}_{\text{click}\to\text{buy}}$):

| Parameter | Conservative (1.5%) | Base Case (2.5%) | Optimistic (3.8%) |
| :--- | :--- | :--- | :--- |
| **Assumed Click-to-Buy CR** | 1.5% | 2.5% | 3.8% |
| **Blended Affiliate Commission / Order** | ₹144.30 ($1.74) | ₹144.30 ($1.74) | ₹144.30 ($1.74) |
| **Expected Revenue per Buy Click** | ₹2.16 ($0.026) | ₹3.61 ($0.0435) | ₹5.48 ($0.066) |
| **Weekly Pilot Buy Clicks / User** | 0.22 clicks | 0.22 clicks | 0.22 clicks |
| **Expected Weekly Revenue / User** | **₹0.48 ($0.0057)** | **₹0.79 ($0.0096)** | **₹1.21 ($0.0145)** |

### Steady-State Break-Even Analysis (at 2,000+ Active Users, ₹11.60 / user / week cost):

$$\text{Break-Even Buy Clicks / Week} = \frac{\text{Marginal Cost per User}}{\text{Expected Revenue per Click}} = \frac{\text{₹11.60}}{\text{Expected Revenue per Click}}$$

- **Under Base Case (2.5% CR $\rightarrow$ ₹3.61 / click)**:
  - Required Outbound Clicks: **3.2 buy clicks / user / week**.
  - Current Pilot Observed Clicks: **0.22 buy clicks / user / week**.
  - **Gap**: Pure affiliate commission with 0.22 clicks/week covers ~7% of commercial variable cost, requiring either higher click intent or a hybrid monetization strategy.

---

## 4. Strategic Commercial Takeaways

1. **Affiliate Commission Alone is Insufficient at Low Purchase Frequency**:
   - Relying exclusively on merchant affiliate payouts (~7.8%) requires high shopping volume or high click-through rates (>3 clicks/week).
   - In fashion styling, users try on multiple garments for exploratory enjoyment before buying one item per month.
2. **High-Margin Value Proposition for Brands (Phase 11 Opportunities)**:
   - Brands currently spend ₹300–₹500 CAC in digital ads with a 15–25% return rate due to sizing uncertainty.
   - FashXStudio drastically reduces sizing returns. Premium merchant listing fees (sponsored brand placements, featured drop collections) and B2B White-Label Styling SDKs offer 10x higher revenue margins than passive affiliate link-outs.
3. **Next Steps for Revenue Reconciliation**:
   - At Day 60, pull validated affiliate reports from networks matching sub-ID prefixes to reconcile actual realized conversion rates against this base model.
