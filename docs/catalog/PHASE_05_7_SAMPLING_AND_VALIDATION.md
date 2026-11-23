# Phase 05.7 — Sampling, Validation, and SSRF Safety Procedures

## 1. Overview
Evaluating catalog freshness and destination link integrity across tens of thousands of garments requires statistically sound, reproducible sampling methods combined with strict security controls against Server-Side Request Forgery (SSRF).

---

## 2. Sampling Methodology

### 2.1 Deterministic & Reproducible Sampling
To ensure evaluations can be audited, verified by third parties, and repeated with identical outputs:
- Every sampling procedure requires a deterministic random seed (default `42`).
- Python's `random.Random(seed)` is isolated to the sampling instance and does not alter global RNG state.
- Offers are sorted by immutable unique identifiers (`id`) prior to sample selection:
  ```python
  sorted_items = sorted(items, key=lambda x: str(x.id))
  rng = random.Random(random_seed)
  return rng.sample(sorted_items, sample_size)
  ```

### 2.2 Stratified Sampling Across Merchants
When evaluating a multi-merchant catalog:
- Offers are grouped into merchant strata (`merchant_id`).
- Quotas are allocated proportionally to each merchant's share of active offers:
  $$n_m = \max\left(1, \left\lfloor n \times \frac{N_m}{N} \right\rfloor\right)$$
- If rounding causes the sample size to diverge from $n$, residual slots are filled round-robin from larger strata.

---

## 3. Server-Side Request Forgery (SSRF) Protection

### 3.1 Destination URL Security Validation
Catalog destination URLs point to external retailer websites. The link verification engine must never allow outbound connections to internal services, local networks, or cloud metadata endpoints.

Before issuing any HTTP probe (`safe_check_product_link`), the engine resolves the domain name via DNS and checks all resulting IP addresses:
1. **Allowed Schemes:** Strictly `http` and `https`.
2. **Blocked Hostnames:** `localhost`, `127.0.0.1`, `::1`, and local cloud metadata hostnames (`169.254.169.254`, `metadata.google.internal`).
3. **Restricted IP Ranges Blocked:**
   - Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
   - Loopback (`127.0.0.0/8`, `::1`)
   - Link-local addresses (`169.254.0.0/16`, `fe80::/10`)
   - Multicast & broadcast (`224.0.0.0/4`, `ff00::/8`)
   - Unspecified / 0.0.0.0 / Reserved IPs

### 3.2 Redirect Safety
HTTP redirects (301, 302, 307, 308) are not followed automatically.
The `Location` header is inspected, and its target destination is re-validated through `validate_url_ssrf_safety`. If a merchant URL attempts to redirect into an internal IP address or disallowed scheme, the link is immediately classified as `INVALID_REDIRECT` and terminated.

---

## 4. Multi-Currency Retention Standard
1. Catalog products may originate from international sources with diverse billing currencies (e.g. `INR`, `USD`, `EUR`, `GBP`).
2. FashXStudio strictly retains each offer's native currency code without implicit or automatic FX conversions during freshness verification.
3. Pricing freshness measures the currency and `price_minor` verified at the source against the last verification timestamp.
