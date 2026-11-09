# RC10-C: Catalog Quality and Freshness Optimization

## 1. Objectives
FashX relies on third-party fashion partner feeds and verified merchant products. Inaccurate sizing, stale prices, uncleared source assets, or broken image URLs directly undermine consumer trust.

## 2. Quality Dimensions
| Dimension | Validation Requirement | Enforcement Tool |
| :--- | :--- | :--- |
| **Source Clearance** | `source_clearance == True` authorized by partner | `scripts/rc10/evaluate_catalog.py` |
| **Product Identity** | `merchant_id`, `source_product_id`, `canonical_product_id` | `evaluate_product()` |
| **Category & Attributes** | Valid garment category mapping (e.g. top, bottom, dress) | Category normalizer |
| **Price & Currency** | Price $> 0$, ISO currency code (`INR`, `USD`) | `evaluate_product()` |
| **Price Freshness** | Timestamp updated within 24 hours ($\le 24\text{ h}$) | `evaluate_product()` |
| **Image Reference** | Non-empty URI to accessible private/public storage | Image validator & HTTP HEAD |

## 3. Evaluation Tooling
The evaluation script [`scripts/rc10/evaluate_catalog.py`](file:///c:/Users/ASUS/Documents/FashXStudio/scripts/rc10/evaluate_catalog.py) flags uncleared sources, stale prices, missing images, and invalid values:
```python
from scripts.rc10.evaluate_catalog import evaluate_product

result = evaluate_product(product_dict, max_price_age_hours=24)
if not result.passed:
    print(f"Product flagged: {result.errors}")
```

## 4. Exit Criteria for Beta
- 100% of presented products have verified source clearances.
- No stale prices ($>24\text{ h}$) served in discovery feeds.
- Zero broken image links or unmapped categories in active feeds.
