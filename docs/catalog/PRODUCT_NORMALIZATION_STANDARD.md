# Product Normalization Standard

## 1. Scope & Normalization Principles

External source catalogs exhibit broad differences in data structures, casing, and formats. FashXStudio enforces strict normalization standards before persisting data.

---

## 2. Specific Normalization Specifications

### 2.1 Identifiers (`source_product_id`)
- **Unicode**: Normalization Form KC (NFKC).
- **Control Characters**: All non-printable and ASCII control characters (`\x00`–`\x1f`, `\x7f`–`\x9f`) are stripped.
- **Length**: Truncated or rejected if exceeding 255 characters.
- **Casing**: Case-preserving to maintain exact parity with merchant ERP/inventory systems.

### 2.2 Brand Names
- Never infer brand names from the product title.
- Unicode NFKC normalized, whitespace collapsed, max 120 chars.
- Common generic placeholders (`unknown`, `n/a`, `na`, `none`, `generic`) are converted to `None`.
- Entity suffixes (`Pvt Ltd`, `LLC`, `Inc.`, `Corp`, `Co.`) are stripped.
- De-duplicated across catalog via case-insensitive `normalized_name`.

### 2.3 Taxonomy & Category Resolution
- Category resolution maps raw category strings to canonical taxonomy: `tops`, `bottoms`, `dresses`, `outerwear`, etc.
- **Zero Fallback Invariant**: Raw category strings that cannot be mapped are flagged with `category_unmapped` and quarantined. **Never fall back silently to `tops/shirt`**.

### 2.4 Currency and Pricing
- Prices are stored as integers representing minor currency units (`price_minor`).
- Minor units are calculated using exact `Decimal` arithmetic and ISO 4217 currency exponents:
  - `INR`: 2 decimals (`1499.00` → `149900`)
  - `USD`: 2 decimals (`19.99` → `1999`)
  - `EUR`: 2 decimals (`25.50` → `2550`)
  - `GBP`: 2 decimals (`15.00` → `1500`)
  - `JPY`: 0 decimals (`1500` → `1500`)
- `to_minor_units()` uses `ROUND_HALF_UP` and rejects non-finite, zero, or negative numbers.

### 2.5 Colors & Indian Apparel Mappings
- Colors are normalized into a two-tuple: `(raw_color_cleaned, canonical_family)`.
- Indian ethnic shades are explicitly resolved to standard families:
  - `mehendi` / `mehndi` / `pista` / `olive` → `Green`
  - `rani pink` / `baby pink` / `rose` / `magenta` → `Pink`
  - `wine` / `maroon` / `crimson` / `burgundy` → `Red`
  - `mustard` / `ochre` → `Yellow`
  - `rust` / `peach` / `coral` → `Orange`
  - `navy` / `indigo` / `sky blue` / `royal blue` / `teal` → `Blue`
  - `off white` / `cream` / `ivory` / `beige` → `White`

### 2.6 Sizes
- Normalized to standard alpha tokens: `XXS`, `XS`, `S`, `M`, `L`, `XL`, `XXL`, `2XL`, `3XL`, `4XL`.
- Universal size variants (`FREE SIZE`, `ONE SIZE`, `FREESIZE`, `FS`, `OS`, `UNIVERSAL`) resolve to `ONE_SIZE`.
- Numeric sizes (`28`, `30`, `32`, `34`, `36`) are preserved.

### 2.7 URL Sanitization & Attribution
- Outbound product links are sanitized to strip tracking parameters:
  - `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, `fbclid`, `pf_rd_r`, `pf_rd_p`.
- Attribution and affiliate tracking parameters are strictly preserved:
  - `tag`, `ref`, `ref_`, `affid`, `aff_id`, `clickid`, `click_id`, `subid`, `sub_id`.
