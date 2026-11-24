# Unsupported Category Policy & Graceful Degradation

## 1. Initial Category Classification

Based on provider capability boundaries and complexity in Indian apparel:

| Garment Category | Initial Classification | Release Status |
|---|---|---|
| **T-Shirts** | Candidate (P0) | Eligible for evaluation |
| **Casual Shirts** | Candidate (P0) | Eligible for evaluation |
| **Basic Kurtas** | Controlled Evaluation (P1) | Eligible for evaluation |
| **Women's Tops** | Controlled Evaluation (P1) | Eligible for evaluation |
| **Dresses** | Controlled Evaluation (P1) | Separate model tuning required |
| **Trousers / Bottoms** | Separate Pipeline (P1) | Separate lower-body model |
| **Sarees** | **Restricted / Blocked (P2)** | **BLOCKED** until multi-piece drape proven |
| **Lehengas** | **Restricted / Blocked (P2)** | **BLOCKED** until multi-piece drape proven |
| **Multi-Piece Layered Sets**| **Restricted / Blocked (P2)** | **BLOCKED** until multi-piece drape proven |

---

## 2. API Enforcement & Shopper Presentation

When a shopper requests a virtual try-on for an unapproved or blocked category:
- The API gate intercepts the request **before** image validation, queuing, or budget reservation.
- HTTP `422 Unprocessable Entity` or `400 Bad Request` is returned with:
  ```json
  {
    "error": "category_unsupported",
    "message": "Virtual try-on is not currently available for this garment type (sarees). You can still view the product details and merchant listing."
  }
  ```
- No silent fallback or mapping to Western categories is permitted.
