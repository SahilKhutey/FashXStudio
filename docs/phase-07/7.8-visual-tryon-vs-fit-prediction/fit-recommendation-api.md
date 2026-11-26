# Fit Recommendation API Specification

> **Endpoint contracts, request/response models, and error codes.**

## 1. Endpoints Overview
- `POST /api/v1/fit/recommendations`: Submit shopper measurements and product identifiers to evaluate fit.
- `GET /api/v1/fit/recommendations/{recommendation_id}`: Retrieve an existing fit recommendation.
- `GET /api/v1/products/{product_id}/size-chart`: Retrieve merchant size chart independently.

## 2. Fit Recommendation Request
```json
{
  "product_id": "00000000-0000-0000-0000-000000000001",
  "merchant_offer_id": "00000000-0000-0000-0000-000000000002",
  "category": "casual_shirts",
  "shopper_measurements": {
    "user_id": "00000000-0000-0000-0000-000000000003",
    "chest_cm": 98.0,
    "waist_cm": 82.0,
    "consent_verified": true
  }
}
```

## 3. Response Schema
```json
{
  "recommendation_id": "fitrec_a1b2c3d4e5f6",
  "product_id": "00000000-0000-0000-0000-000000000001",
  "merchant_offer_id": "00000000-0000-0000-0000-000000000002",
  "outcome": "RECOMMENDED",
  "recommended_size": "M",
  "alternative_sizes": [],
  "explanation_code": "BEST_FIT_MATCH",
  "explanation_message": "Size M is recommended based on chest measurement and ease tolerance.",
  "fit_model_version": "v1.0.0",
  "evidence": [
    {
      "source_type": "SHOPPER_MEASUREMENT",
      "source_id": "00000000-0000-0000-0000-000000000003",
      "source_revision": "v1"
    },
    {
      "source_type": "MERCHANT_SIZE_CHART",
      "source_id": "sc_001",
      "source_revision": "rev_2026_01"
    }
  ],
  "fit_guaranteed": false,
  "disclaimer": "Fit guidance is estimated from verified merchant size charts and shopper measurements. It is not a guarantee of fit."
}
```
