# Economic Sensitivity Models: Path A, Path B, and Path C

**Purpose**: Quantitative financial comparison of three strategic monetization trajectories (Consumer Affiliate, B2B Brand Fit Widget, and Hybrid Model) using pilot telemetry and real brand cost data.

---

## 1. Path A: Consumer-First App (Affiliate Monetization)

### Formula:
$$\text{Revenue / User / Month} = \text{Clicks / Month} \times \text{Conversion Rate} \times \text{AOV} \times \text{Commission Rate}$$
$$\text{Cost / User / Month} = (\text{Tries / Month} \times \text{Cost / Try}) + \text{Infra Share} + \text{Enrichment} + \text{Support}$$

### Empirical Inputs from Phase 10 Pilot:
- Outbound Buy Clicks / User / Month: **0.90 clicks** (0.22 clicks / week $\times 4.1$)
- Try-ons / User / Month: **5.5 try-ons** (1.35 tries / week $\times 4.1$)
- Try-on Inference Cost: **$0.065 / try** (~₹5.40 INR)
- Average Order Value (AOV): **₹1,850 INR** (~$22.30 USD)
- Weighted Blended Commission Rate: **7.8%** (~₹144.30 INR per validated order)
- Monthly Serving Cost at Scale (2,000+ users):
  - Inference: $5.5 \times \$0.065 = \mathbf{\$0.358}$ (~₹29.70)
  - Infra + Enrichment + Messaging: **$0.080** (~₹6.64)
  - **Total Cost per Active User per Month**: **$0.438** (~₹36.35 INR)

### Sensitivity Table (Path A):

| Case | Assumed Click-to-Buy CR | Monthly Revenue / User | Monthly Cost / User | Net Monthly Contribution | Blended CAC (Acquisition) | Payback Period |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Low** | 1.5% | ₹1.95 ($0.023) | ₹36.35 ($0.438) | **-₹34.40 (-$0.415)** | ₹180 ($2.17) | **Never (Negative Unit Margin)** |
| **Base** | 2.5% | ₹3.25 ($0.039) | ₹36.35 ($0.438) | **-₹33.10 (-$0.399)** | ₹120 ($1.45) | **Never (Negative Unit Margin)** |
| **High** | 4.0% | ₹5.20 ($0.063) | ₹36.35 ($0.438) | **-₹31.15 (-$0.375)** | ₹80 ($0.96) | **Never (Negative Unit Margin)** |

### Break-Even Requirement for Path A:
To achieve breakeven (covering ₹36.35/user/month cost), an active user must generate:
- At 2.5% CR: **10.1 outbound buy clicks per month** (vs. 0.90 observed in pilot $\rightarrow$ **11.2x increase needed**), OR
- At 0.90 clicks/month: An astronomical conversion rate of **28.0%** (industry benchmark is 1.5–3.0%).
- **Lean Team Break-Even** (₹3,00,000/mo founder burn): Impossible on pure affiliate commissions without hundreds of thousands of active users.

> [!CAUTION]
> **Path A Verdict**: Pure consumer affiliate revenue is commercially insolvent at early-to-mid scale. The high inference cost per try-on (€0.065) fundamentally exceeds the micro-commission of occasional affiliate checkouts.

---

## 2. Path B: Brand-First B2B (Fit & Try-On Widget for D2C Brands)

### Formula:
$$\text{Brand Value / Month} = \text{Monthly Orders} \times \text{Size Return Reduction} \times \text{Cost per Return}$$
$$\text{Cost to Serve / Brand} = (\text{Orders with Try-On} \times \text{Tries / Order} \times \text{Cost / Try}) + \text{Hosting \& Support}$$

### Real Industry Inputs (from Brand Founder Interviews in Section 11.9):
- D2C Fashion Brand Monthly Orders: **2,500 orders / month** on brand Shopify store.
- Baseline Return Rate: **30.0%** (750 returns / month).
- Share of Returns Due to Size / Inconsistent Fit: **65.0%** (488 size returns / month).
- All-in Cost per Return: **₹350 INR** (~$4.20 USD, covering forward + reverse logistics, return shipping subsidy, quality check inspection, damaged packaging, and markdown on restocked inventory).
- Target Size Return Reduction: **4.0 percentage points** (reducing size returns from 19.5% to 15.5% of total orders = **100 fewer returns per month**).
- **Monthly Savings Delivered to Brand**: $100 \times \text{₹350} = \mathbf{\text{₹35,000 INR / month}}$ (~$420 USD / month).

### Pricing & Margins:
- **Pricing Model**: Flat B2B SaaS Tier: **₹15,000 INR / month** ($180 USD) for stores up to 3,000 orders/month (brand captures ₹20,000 net monthly ROI).
- **Cost to Serve Brand**:
  - ~20% of shoppers engage try-on widget on product page = 500 shoppers.
  - Average 2.2 tries per shopping session = 1,100 generations.
  - 1,100 generations $\times$ ₹5.40 ($0.065) = **₹5,940 INR / month** ($71.50).
  - Infrastructure + support: **₹1,500 INR / month** ($18.00).
  - **Total Cost to Serve**: **₹7,440 INR / month** ($89.50).
- **Net Contribution Margin per Brand**:
  $$\text{Contribution} = \text{₹15,000} - \text{₹7,440} = \mathbf{\text{₹7,560 INR / month}} \ (\approx \mathbf{50.4\% \text{ Gross Margin}})$$

### Lean Team Break-Even for Path B:
- Lean Team Burn: **₹2,50,000 INR / month** (~$3,000 USD for solo founder + cloud).
- **Brands Needed for Cash Break-Even**:
  $$\frac{\text{₹2,50,000}}{\text{₹7,560 net contribution}} \approx \mathbf{33 \text{ Active D2C Brands}}$$
- With founder-led sales and warm introductions, 33 brands is an achievable 9–12 month B2B milestone.

---

## 3. Path C: Hybrid Model (Consumer App + Brand Placement / Fit Insights)

### Structure:
- Consumer app remains the high-trust styling and fit-profile discovery engine (generating rich user body silhouette data, size feedback ledger, and purchase intent).
- Monetization combines:
  1. Performance affiliate links on general catalog (Path A baseline: ~₹3.25 / user / month).
  2. **Sponsored Brand Product Drops** (₹25,000 / drop for curated feature in recommendation feed).
  3. **Brand Fit Analytics Portal** (brands pay ₹10,000/month to access anonymized aggregate fit feedback comparing their sizing against competitors).
- **Trust Safeguard**: Sponsored listings must carry explicit, non-removable `[Sponsored]` chips; MMR ranker retains hard filters (size, budget) regardless of sponsorship bids to preserve feed truthfulness.

---

## 4. The Three Numbers That Must Be True (Per Path)

### Path A (Consumer Affiliate)
1. **Clicks per User**: Active users must generate at least **4.5 outbound buy clicks / month** (5x current pilot rate).
2. **Affiliate Conversion**: Validated click-to-purchase conversion rate must exceed **3.5%**.
3. **Blended CAC**: Organic WhatsApp / look-sharing loop must keep blended CAC below **₹40 INR** ($0.48).

### Path B (Brand-Paid B2B)
1. **Measurable Return Reduction**: The widget must measurably cut size-related returns by at least **3.0 percentage points** in a 30-day A/B store test.
2. **Brand Willingness to Pay**: Brands must be willing to pay at least **₹12,000 to ₹18,000 INR / month** for the fit & try-on widget.
3. **Sales Cycle**: Founder-led B2B sales cycle must close within **< 30 days** using Shopify app store distribution and warm network intros.

### Path C (Hybrid)
1. **Active Consumer User Base**: App must sustain at least **2,500 monthly active users** to justify brand drop sponsorship fees.
2. **Brand Placement Demand**: At least **3 D2C brands per month** pay for sponsored drop placements at ₹25,000/drop.
3. **Zero Erosion of Feed Trust**: Negative feedback signals on sponsored items must remain below **10.0%** to prevent audience attrition.
