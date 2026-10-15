# Strategic Decision Memo: Transition to Brand-First B2B (Phase 11)

**Date**: October 2026  
**Document Length**: 3 Pages  
**Decision Gate Review Date**: Week 6 (Checkpoint 1) and Week 13 (Final Gate)  
**Status**: APPROVED & ADOPTED

---

## 1. The Decision

### **VERDICT: PIVOT TO PATH B (Brand-First B2B: AI Fit Intelligence & Sizing Return Reduction for Indian D2C Fashion Brands).**

We will pivot from operating a standalone B2C consumer shopping app monetized via affiliate links to packaging our validated sizing intelligence, catalog normalization, and visual try-on engine into an **embeddable B2B SaaS widget and analytics dashboard for Indian D2C apparel brands**.

The consumer mobile app is preserved as a live innovation sandbox, consumer demographic benchmark engine, and interactive sales demo, but engineering and commercial focus shifts 100% to serving merchant stores on Shopify.

---

## 2. The Evidence in Five Key Bullets

1. **Affiliate Unit Economics are Negative; B2B ROI is Immediate**: The pilot confirmed that consumer affiliate commissions generate only ~₹3.25/active user/month against a serving cost of ₹36.35/user/month (net contribution -₹33.10). Conversely, brand interviews confirmed that an Indian fashion brand loses **₹350 out-of-pocket on every single return**, creating an immediate, verifiable willingness to pay **₹15,000 to ₹25,000/month** for a tool that reduces returns by even 3–4 points.
2. **Generic Visual Try-On is a Free Commodity; Indian Sizing Fit is a Moat**: Google launched free virtual try-on on Google Shopping in India in Dec 2025. In our blind benchmark, Google matches western tops (4.40 vs 4.25), but **FashXStudio is dramatically superior on Indian ethnic silhouettes (4.20 vs 3.45 on kurtas, 3.85 vs 2.60 on draped sarees)** and incorporates brand-specific chest/waist measurements that Google's visual model ignores.
3. **Core Engine Architecture is Validated and Production-Ready**: Phase 10 proved our backend stability: **99.57% crash-free sessions** across 920 sessions, **94.88% try-on completion**, **14.1s P95 generation latency**, and **0 security/privacy incidents**. Packaging this into an embeddable widget requires no architectural rewrite—only an SDK wrapper around existing `/tryon` and `/recommendations` endpoints.
4. **Brands Suffer from a Massive, Quantified P&L Crisis**: 5 out of 5 interviewed D2C brand operators reported return rates between **21% and 36%**, with **65% to 75%** of return tickets citing incorrect size or fit. Every brand confirmed direct operational ownership of the problem and expressed active willingness to pilot.
5. **Clear Co-Founder Value Proposition**: Sponsoring a consumer app required a nebulous "growth hacker" competing with massive venture-funded ad budgets. Sponsoring a B2B SaaS solution creates a well-defined mandate for an experienced **B2B GTM / Commercial Co-Founder** with warm doors into Indian fashion brands.

---

## 3. Scorecard Result & Runner-Up

- **Winning Strategy**: **Option B: Brand-First B2B** $\to$ **435 / 500 points**.
- **Runner-Up**: **Option D: Niche Ethnic Wedge** $\to$ **375 / 500 points** (-60 points / -16.0%).
- **Key Distinction**: Option B wins cleanly beyond the 10% tie-breaker threshold. Furthermore, Option B directly integrates Option D's ethnic-wear technical advantage as its primary initial customer segment (targeting modern ethnic wear brands like FabIndia partners, Snitch, and Libas where return costs are highest).

---

## 4. The Red-Team Challenge & Our Answer

- **The Challenge**: *"Brands will demand 60-day free pilots, bog you down in custom theme debugging, and churn if returns don't immediately drop by 5%."*
- **Our Answer**:
  1. We provide an unlisted, 1-click Shopify App Store wrapper (no manual theme editing required).
  2. We limit pilots strictly to 30 days on a pre-agreed sample of 5 top-selling, high-return SKUs with pre-logged baseline return numbers.
  3. We position the product as **"AI Fit Intelligence & Return Reduction"** (funded from logistics/operations budgets), rather than a marketing "try-on gimmick".
  4. Base tiers include 1,500 try-ons/month with automated overage pricing to protect gross margins against flash-sale traffic spikes.

---

## 5. The Three Numbers That Must Be True (with Target Dates)

| # | Metric / Number That Must Be True | Benchmark Threshold | Date to Check |
| :--- | :--- | :--- | :--- |
| **N1** | **Design-Partner Pilot Signups** | At least **3 Indian D2C fashion brands** sign and install the 30-day measured pilot. | **Day 45** (Mid-Plan Checkpoint) |
| **N2** | **Measurable Return Reduction** | Measured size-related return rate on pilot SKUs decreases by at least **$\ge 3.0$ percentage points** vs. pre-pilot baseline. | **Day 75** (Post-Pilot Audit) |
| **N3** | **Paid Commercial Conversion** | At least **2 of the 3 pilot brands** convert to a paid subscription ($\ge \text{₹15,000/month}$). | **Day 90** (End of Phase 11) |

---

## 6. Explicit Kill Criteria

If any of the following kill criteria occur, we immediately halt the B2B SaaS trajectory and execute the designated fallback:

1. **Brand Acquisition Failure**: If after **45 days** of founder-led outreach (with $\ge 25$ qualified brand conversations), fewer than **2 brands** agree to install the 30-day trial $\to$ **KILL B2B PATH; Pivot to Option D (Niche Ethnic B2C Wedge) or execute Option E (Archive & Conclude).**
2. **Zero Return Reduction**: If across 3 pilot brands, the measured return reduction on test SKUs is **$< 1.5$ percentage points** $\to$ **KILL PRODUCT OFFERING; Conclude that visual/measurement AI does not alter consumer return behavior.**
3. **Severe Churn / Zero Paid Conversion**: If at Day 90, **0 out of 3 pilot brands** convert to a paid tier citing lack of ROI $\to$ **SHELVE VENTURE CLEANLY (Option E).**

---

## 7. What We Are Deliberately NOT Doing

1. **NO Paid Consumer User Acquisition**: Zero ad spend on Meta or Google Ads for the B2C mobile app.
2. **NO Commerce / Checkout Modules (C05–C11 Remain Frozen)**: We do not process orders, collect payments, or manage inventory. We remain an intelligence layer on top of merchant checkouts.
3. **NO Multi-Garment Stacking (F06)**: We focus exclusively on single-garment sizing accuracy for high-return items (kurtas, dresses, shirts).
4. **NO Broad Enterprise Sales**: Zero outreach to massive conglomerates (Reliance, Aditya Birla) with 9-month procurement cycles. Focus strictly on agile D2C Shopify brands (₹5 Cr to ₹50 Cr GMV).

---

## 8. Strategy Review Dates

- **Mid-Point Gate Review**: **Week 6 (Day 45)** $\to$ Evaluate Number N1 (Pilot Signups).
- **Final Strategy Gate Review**: **Week 13 (Day 90)** $\to$ Evaluate Numbers N2 and N3 (Return Reduction and Paid Conversions).
