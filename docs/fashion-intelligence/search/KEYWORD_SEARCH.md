# Keyword Search Specification

## 1. Overview
Keyword search executes full-text searches across product titles, descriptions, brand names, and approved fashion attributes using PostgreSQL Full-Text Search (`tsvector`, `tsquery`) with weight prioritization.

---

## 2. Text Normalization & Query Processing
Before querying the database, search queries undergo multi-stage normalization:
1. **Length Limitation**: Maximum 200 characters; longer queries are rejected with HTTP 422.
2. **Whitespace & Case Normalization**: Whitespace collapsed; lowercase conversion.
3. **Punctuation Sanitization**: Punctuation safely removed or tokenized; SQL injection tokens (`'`, `--`, `;`) strictly neutralized.
4. **Synonym Expansion**: Words looked up in `search_synonyms` (e.g. "tee" $\leftrightarrow$ "t-shirt", "kurti" $\leftrightarrow$ "short kurta").
5. **Typo Tolerance**: Trigram matching (`similarity()` via `pg_trgm`) applied if standard full-text matching yields zero results.

---

## 3. Weighting Hierarchy
The PostgreSQL GIN index ranks candidate documents based on field importance:
- **Weight A (1.0)**: Product Title, Brand Name.
- **Weight B (0.4)**: Garment Type, Color, Occasion, Category Name.
- **Weight C (0.2)**: Pattern, Verified Fabric.
- **Weight D (0.1)**: Raw Merchant Product Description.

Title and brand matches consistently rank higher than incidental matches buried deep inside product descriptions.
