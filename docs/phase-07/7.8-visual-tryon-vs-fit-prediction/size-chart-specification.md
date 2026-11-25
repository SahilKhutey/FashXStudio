# Merchant Size-Chart Specification & Provenance

> **Catalog schema, data ingestion, and provenance tracking.**

## 1. Measurement Basis
Every merchant size chart must explicitly state its measurement basis:
- **`BODY`**: The dimensions describe the shopper's body measurements that the garment is designed to accommodate.
- **`GARMENT`**: The dimensions describe the actual cut and finished physical measurements of the garment itself (which includes ease allowance).

FashXStudio prohibits assuming or converting between `BODY` and `GARMENT` without merchant-documented ease specifications.

## 2. Measurement Units
- Standard supported units: `CM` and `INCH`.
- Normalization: Ingestion standardizes values to centimeters for internal matching while preserving original merchant values.

## 3. Schema Structure
```python
class MerchantSizeChartResponse(BaseModel):
    chart_id: str
    merchant_id: str
    merchant_name: str
    merchant_product_id: str
    canonical_garment_id: str | None
    basis: MeasurementBasis  # BODY | GARMENT
    unit: MeasurementUnit    # CM | INCH
    status: SizeChartStatus  # VERIFIED | UNVERIFIED | STALE | WITHDRAWN
    is_stale: bool
    source_reference: str
    source_revision: str
    rows: list[SizeChartRow]
```

## 4. Ingestion Validation Rules
1. Non-empty size rows with positive numeric dimensions.
2. No duplicate size rows without controlled reconciliation.
3. Verification timestamp tracked; charts older than 90 days are flagged as `STALE`.
4. LLM-based hallucination of missing size measurements is strictly prohibited.
