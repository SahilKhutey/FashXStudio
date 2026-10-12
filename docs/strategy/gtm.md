# Go-to-Market Strategy: Brand-First B2B (Path B)

**Strategic Focus**: AI Fit Intelligence & Size-Return Reduction Engine for Indian D2C Apparel Brands  
**Runner-Up Strategy Note**: Sits alongside Option D (Ethnic Wear Niche Wedge), which serves as our initial target segment within B2B.

---

## 1. Ideal Customer Profile (ICP)

| Attribute | Definition / Target Window | Rationale |
| :--- | :--- | :--- |
| **Geography** | India (Tier 1 & Tier 2 D2C brands, headquartered in Delhi NCR, Mumbai, Bengaluru, Jaipur). | Shared domestic logistics pain; highest return costs. |
| **Store Platform** | Shopify / Shopify Plus. | Standardized Liquid/Theme API; enables rapid 1-click app installation. |
| **Monthly Order Volume** | **1,500 to 10,000 orders / month** (Annual GMV: ₹5 Cr to ₹35 Cr). | Large enough to see statistically significant return reductions in 30 days; agile enough for founder-level decision making. |
| **Garment Category** | Modern ethnic wear (kurtis, anarkalis), tailored women's western wear, plus-size apparel, and structured men's shirts. | Categories with the highest historical return rates (30–40%) and high fit complexity. |
| **Executive Buyer** | Founder / CEO, Head of Operations, or Head of E-commerce. | Executives whose primary KPI is reducing logistics burn and expanding gross margins. |

---

## 2. The Commercial Offer & 30-Day Measured Pilot

We do not sell abstract AI technology; we sell **verifiable reverse-logistics margin recovery**.

### Offer Structure:
- **Pilot Duration**: **30 Days** on the brand's **Top 5 High-Return SKUs**.
- **Commercial Terms**: **Free for 30 Days** (or token ₹5,000 setup fee), converting to a paid tier upon hitting pre-agreed success criteria.
- **Mutual Success Contract**:
  - We pre-record the 60-day baseline return rate on the 5 pilot SKUs (typically 32–38%).
  - We install the embeddable fit recommendation card and visual try-on overlay on those 5 product pages.
  - Success is defined in writing: **$\ge 3.0$ percentage point reduction in size-related returns** OR **$\ge 8.0\%$ increase in product page add-to-cart conversion**.
  - Upon achieving the target, the brand converts to the standard subscription tier: **₹15,000 / month** (up to 2,500 orders) or **₹25,000 / month** (up to 6,000 orders).

---

## 3. Product Architecture Changes (Transition to Multi-Tenant B2B)

The underlying core engine (built and validated across Phases 5 through 9) is 100% reused. We add five specific B2B interfaces:

1. **Lightweight Embeddable Storefront SDK (`fashx-widget.js`)**:
   - Zero-dependency, `< 45KB` script tag injected into the brand's Shopify product display page (PDP).
   - Asynchronously loads adjacent to the size selector; zero impact on Google Core Web Vitals (adds $< 80\text{ms}$ load time).
2. **Merchant Fit & Configuration Dashboard (`/merchant/dashboard`)**:
   - Multi-tenant brand portal where merchants map their bespoke brand size charts (chest, waist, hip, length in cm/inches).
   - Real-time visualization of returns prevented, try-on sessions, and shopper sizing distribution.
3. **Automated Return Analytics Attribution**:
   - Injects `fashx_fit_token` into the Shopify checkout order attribute, allowing automated reconciliation with return tickets inside the merchant's ERP/Shopify orders export.
4. **Usage Tier Caps & Circuit Breakers**:
   - Automatic throttling and fallback to lightweight size card when monthly inference quotas are met, protecting gross margins during flash sales.

---

## 4. Legal & Regulatory Architecture (DPDP Vendor Role Shift)

Under India's **Digital Personal Data Protection (DPDP) Act 2023**:
- In Phase 8/10 (Consumer App), FashXStudio acted as the **Data Fiduciary**.
- In Path B (B2B SaaS Widget), **the Brand is the Data Fiduciary**, and **FashXStudio acts as the Data Processor**.

### Legal Safeguards Required Before Brand Go-Live:
- **B2B Data Processing Agreement (DPA)**: Standardized vendor DPA signed with every partner merchant stipulating:
  - 100% prohibition on using shopper photographs or biometric measurements for third-party model retraining.
  - Mandatory 72-hour automated purge of temporary inference images.
  - Strict data localization within AWS Mumbai (`ap-south-1`).
  - Standard breach notification clock (informing the fiduciary within 12 hours).

---

## 5. Sales Motion & Target Pipeline (First 90 Days)

- **Sales Motion**: Founder-Led Sales $\to$ Transition to GTM Co-Founder by Month 2.
- **Distribution Channels**:
  1. **Phase 6 Partner Warm Network**: Leverage existing direct catalog relationships (FabIndia partners, Snitch, Westside ecosystem). Target: **3 signed design partners in Month 1**.
  2. **Shopify D2C Community & WhatsApp Operator Groups**: Direct outreach to e-commerce heads citing specific return benchmarks.
  3. **Unlisted Shopify App Store Listing**: Frictionless 1-click installation to eliminate custom theme integration pushback.
- **Pricing Tiers**:
  - **Starter Tier**: ₹15,000 / month (up to 2,500 monthly orders; 1,500 try-ons included).
  - **Growth Tier**: ₹28,000 / month (up to 7,500 monthly orders; 4,000 try-ons included).
  - **Enterprise**: Custom / ₹8 per additional generation overage.

---

## 6. Runner-Up Strategy: Option D (Occasion & Ethnic Wear Niche Wedge)

If B2B brand pilot conversions stall against kill criteria, Option D serves as our immediate strategic fallback:
- Re-orient the consumer app exclusively around high-ticket wedding and festive shopping (where AOV is ₹4,500+ and affiliate commission yields ₹350+ per sale).
- Curate 30 boutique ethnic designers with verified sizing fidelity.
