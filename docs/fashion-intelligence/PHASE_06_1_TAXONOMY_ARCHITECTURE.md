# Phase 06.1 — Fashion Taxonomy Architecture

## 1. Architectural Principles

1. **Separation of Concerns:**
   - **Taxonomy:** The canonical controlled vocabulary and classification tree (defined declaratively in repository YAML and mirrored in database lookup tables).
   - **Enrichment:** The process of mapping, extracting, and assigning taxonomy attributes to products.
   - **Search & Discovery:** Downstream consumers querying indexed product classifications.

2. **Hierarchical Categorization:**
   - Products are classified into strict parent-child categories (`Root -> Subcategory -> Leaf`).
   - Every product record must resolve to a valid leaf category node (`is_leaf = True`) unless explicitly permitted.

3. **Stable Identifiers:**
   - All internal keys, categories, attributes, and allowed values use snake_case identifiers (e.g. `t_shirt`, `crew_neck`, `knee_length`).
   - Human-readable display labels can be translated and localized without modifying database records or breaking foreign keys.

4. **Multi-Source Provenance & Confidence:**
   - Attributes track their origin (`MERCHANT`, `SOURCE_FEED`, `RULE_BASED`, `AI_IMAGE`, `AI_TEXT`, `HUMAN_REVIEW`, `USER_FEEDBACK`).
   - Confidence levels (`0.0` to `1.0`) are preserved independently from attribute values.

5. **Category Applicability:**
   - Attributes must be semantically valid for the garment category. Necklines and sleeves cannot be assigned to footwear or accessories.

## 2. Component Structure

```
backend/fashx/catalog/taxonomy/
├── __init__.py           # Package exports
├── contracts.py          # Pydantic schemas, Enums, and ValueStatus
├── registry.py           # In-memory TaxonomyRegistry with fast lookups
├── loader.py             # YAML schema compiler and validator
├── validator.py          # ProductClassification validator
├── versioning.py         # Semantic versioning and deprecation manager
└── schemas/              # Declarative YAML source-of-truth
    ├── category.yaml
    ├── garment_types.yaml
    ├── occasions.yaml
    ├── audiences.yaml
    ├── colors.yaml
    ├── patterns.yaml
    ├── fabrics.yaml
    ├── sleeves.yaml
    ├── necklines.yaml
    ├── silhouettes.yaml
    ├── indian_wear.yaml
    ├── western_wear.yaml
    ├── footwear.yaml
    ├── accessories.yaml
    └── missing_values.yaml
```

## 3. Database Entity Model

- `taxonomy_versions`: Semantic version releases (`1.0.0`, `ACTIVE`, `en-IN`, `IN`).
- `taxonomy_categories`: Category nodes, paths, levels, and leaf indicators.
- `taxonomy_attributes`: Attribute definitions, types, applicability scopes, and validation rules.
- `taxonomy_attribute_values`: Controlled vocabularies and allowed values.
- `taxonomy_aliases`: Synonyms and merchant jargon mapped to canonical IDs.
- `product_classifications`: Association between `canonical_garments` and taxonomy versions.
- `product_attribute_values`: Product-specific attribute values and status (`KNOWN`, `UNKNOWN`, `NOT_APPLICABLE`).
- `product_attribute_provenance`: Confidence scores, source tracking, and audit review flags.
