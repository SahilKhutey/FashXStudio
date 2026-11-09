# RC13: Unit Economics & Operating Cost Model

## 1. Cost Components per Active User
- **VTO Inference Cost**:
  - Estimated GPU cloud cost: $0.02 – $0.05 per generated try-on (₹1.70 – ₹4.20).
  - Monthly quota: 10–15 free try-ons per pilot user, keeping cloud inference bounded under $0.50 (₹42) per active monthly user.
- **Storage & Infrastructure Cost**:
  - Ephemeral user photo storage: S3 lifecycle policy auto-deletes raw photos after processing. Negligible storage overhead (< $0.01 / user / month).
  - PostgreSQL / pgvector & backend API hosting: Fixed staging tier.

## 2. Monetization Pathways
- **Affiliate Commissions**: 5% – 12% affiliate commission on completed retailer sales via outbound redirect links.
- **Merchant Partner Subscriptions**: Brand placement and featured collection spotlights for verified apparel retailers.
- **Sustaining Model**: At an average order value (AOV) of ₹1,500 – ₹2,500 and a 6% affiliate payout, each converted purchase yields ₹90 – ₹150, comfortably covering the ₹20 – ₹40 try-on engagement cost per active converting shopper.
