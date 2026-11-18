# Product Data Contract

## 1. Specification Overview

The FashXStudio catalog defines strict schemas for external adapter ingestion (`SourceProduct`) and internal canonical persistence (`CanonicalGarment`, `MerchantProduct`, `MerchantOffer`).

---

## 2. External Ingestion Contract (`SourceProduct`)

```python
@dataclass(frozen=True)
class SourceProduct:
    source_slug: str
    source_product_id: str
    title: str
    category: str
    price_minor: int
    currency: str = "INR"
    product_url: str = ""
    brand: str | None = None
    subcategory: str | None = None
    description: str | None = None
    image_url: str | None = None
    in_stock: bool | None = True
    sizes: tuple[str, ...] = ()
    source_updated_at: str | None = None
    image_rights: str = "partner_authorized"
    tryon_rights: bool = False
    prepared_image_key: str | None = None
    prepared_image_hash: str | None = None
    raw_attributes: dict[str, Any] = field(default_factory=dict)
```

### Field Requirements and Constraints

| Field | Type | Mandatory | Validation & Normalization Rules |
| :--- | :--- | :--- | :--- |
| `source_slug` | `str` | Yes | Non-empty slug; must match registered, active catalog source. |
| `source_product_id` | `str` | Yes | NFKC normalized, max 255 chars, control characters stripped, non-empty. Case-preserving. |
| `title` | `str` | Yes | NFKC normalized, max 500 chars, whitespace collapsed, non-empty. |
| `category` | `str` | Yes | Validated against taxonomy. Unmapped values rejected with `category_unmapped`. |
| `price_minor` | `int` | Yes | Integer representation in minor currency units (e.g. 149900 = 1499.00 INR). Must be > 0. |
| `currency` | `str` | Yes | ISO 4217 3-letter currency code (e.g. `INR`, `USD`, `EUR`, `GBP`, `JPY`). |
| `product_url` | `str` | No | Valid HTTPS URL. No embedded credentials. Tracking parameters stripped while preserving affiliate tags. |
| `brand` | `str` | No | Conservative normalization; legal suffixes stripped. Never inferred from title. |
| `image_url` | `str` | No | Valid HTTPS URL. Evaluated against source display rights. |
| `sizes` | `tuple[str, ...]` | No | Normalized to alpha tokens (`XS`, `S`, `M`, `L`, `XL`), numeric waist sizes, or `ONE_SIZE`. |
| `in_stock` | `bool` | No | Defaults to `True` if missing. |

---

## 3. Canonical Domain Entity Mappings

1. **`CanonicalGarment`**: Holds display metadata, canonical taxonomy category/subcategory, price, stock availability, sizes, and virtual try-on eligibility flags.
2. **`MerchantProduct`**: Maps the retailer/merchant identity, source identity, and `source_product_id` to the canonical garment.
3. **`MerchantOffer`**: Represents the point-in-time commercial offer, pricing in minor units, currency, and outbound referral link.
4. **`GarmentImage`**: Stores authorized media assets with content hashes and permissions.
