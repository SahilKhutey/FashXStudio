# Product Policy: Visual Try-On vs. Fit Prediction

> **Product policy and compliance guidelines.**

## 1. Fundamental Distinction
In FashXStudio, Visual Try-On and Fit Prediction are distinct systems with different input requirements, reliability models, and legal disclosures:

| Dimension | Visual Try-On (VTO) | Fit Prediction |
|---|---|---|
| **Primary Goal** | Visual simulation of drape and styling | Quantitative dimensional compatibility |
| **Technology** | Generative diffusion model (e.g. FASHN adapter) | Rule/statistical dimensional comparison |
| **Input Data** | Shopper portrait photo + garment image | Shopper body measurements + merchant size chart |
| **Output Type** | Image (`.jpeg`, watermarked, 2D) | Structured recommendation (`S`, `M`, `L`, etc.) |
| **Authoritative Source** | Provider inference output | Merchant-supplied verified size specifications |
| **Output Label** | `AI-generated visual simulation` | `Fit guidance` or `Unavailable` |
| **Fit Guarantee** | **STRICTLY PROHIBITED** | **STRICTLY PROHIBITED** |

## 2. Invariants
1. **No Fit Claims from Image Generation**: The VTO service must never output `fit_verified=True` or compute an arbitrary "fit score" derived from image pixels.
2. **No Image as Fit Evidence**: The Fit Recommendation Service strictly rejects virtual try-on images as input evidence.
3. **Fail-Closed Availability**: When merchant size charts or shopper measurements are missing, stale, or unverified, the fit service returns `INSUFFICIENT_DATA` or `STALE_SIZE_CHART`. It never guesses a size.
4. **Separation in UI**: The visual try-on display and merchant size chart are rendered in distinct sections.
