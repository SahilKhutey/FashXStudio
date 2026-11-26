# 02 — Sizing System Registry

## 1. Registry Architecture

Sizing systems differ substantially across regions, brands, and categories. A standard "Size 10" in the US is very different from a "Size 10" in the UK, and "Medium" in Asian fits differs from Western cuts.

FashXStudio explicitly registers sizing systems and enforces strict boundaries:
- **No Unverified Regional Conversions**: We never guess or approximate a conversion between sizing systems.
- **Native Merchant Labels Retained**: If a merchant uses a proprietary sizing system or an unverified regional conversion is requested, the system preserves the native merchant size label and tags the response as `UNMAPPED`.

## 2. Standard Registered Systems

| Code | Type | Category | Market | Description | Example Labels |
|---|---|---|---|---|---|
| `INTL_ALPHA` | REGIONAL_STANDARD | GENERAL | GLOBAL | International Alpha | XXS, XS, S, M, L, XL, XXL, 3XL |
| `US_NUMERIC_WOMEN` | REGIONAL_STANDARD | TOPS / DRESSES | US | US Women's Numeric | 00, 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 |
| `US_NUMERIC_MEN` | REGIONAL_STANDARD | TOPS / BOTTOMS | US | US Men's Numeric | 34, 36, 38, 40, 42, 44, 46, 48 |
| `UK_NUMERIC` | REGIONAL_STANDARD | TOPS / DRESSES | UK | UK Numeric Standard | 4, 6, 8, 10, 12, 14, 16, 18, 20 |
| `EU_NUMERIC` | REGIONAL_STANDARD | TOPS / BOTTOMS | EU | European Numeric | 32, 34, 36, 38, 40, 42, 44, 46, 48 |
| `WAIST_INCHES` | REGIONAL_STANDARD | BOTTOMS | GLOBAL | Waist in Inches (Jeans/Trousers) | 26, 28, 30, 32, 34, 36, 38, 40 |
| `COLLAR_INCHES` | REGIONAL_STANDARD | SHIRTS | GLOBAL | Collar Size in Inches | 14, 14.5, 15, 15.5, 16, 16.5, 17 |
| `INDIA_ALPHA` | REGIONAL_STANDARD | GENERAL | IN | India Standard Alpha | XS, S, M, L, XL, XXL |
| `ETHNIC_INDIA` | REGIONAL_STANDARD | ETHNIC | IN | Indian Ethnic (Kurta / Churidar) | 36, 38, 40, 42, 44, 46 |

## 3. Merchant Proprietary Systems
Merchants may define custom proprietary sizing codes (e.g. `MERCHANT_ZARA_WOMEN`, `MERCHANT_HNM_MEN`).
- Sizing definitions include allowed labels in strictly ordered sequence.
- Mapping status is set to `NATIVE` for the merchant's defined labels.
- Cross-system conversion returns `None` unless an authoritative conversion table signed by the merchant is registered.
