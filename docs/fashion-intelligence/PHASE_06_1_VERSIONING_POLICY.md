# Phase 06.1 — Taxonomy Versioning & Migration Policy

## 1. Versioning Semantics

Taxonomy releases follow strict Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR (e.g. 1.0.0 -> 2.0.0):**
  - Breaking structural changes: removing categories or garment types, altering parent-child hierarchy in ways that invalidate paths, or redefining attribute semantics.
- **MINOR (e.g. 1.0.0 -> 1.1.0):**
  - Additive, backward-compatible additions: adding new categories, allowed garment types, new pattern/color shades, or optional attribute extensions.
- **PATCH (e.g. 1.0.0 -> 1.0.1):**
  - Non-semantic changes: correcting typos in display labels, adding translations/locales, or adding synonyms to `taxonomy_aliases`.

## 2. Backward Compatibility Rule

A registry version `R` is compatible with a product classification version `P` if and only if:

$$\text{R.major} == \text{P.major} \quad \text{and} \quad \text{R.minor} \ge \text{P.minor}$$

When the active taxonomy is updated from `1.0.0` to `1.1.0`, existing product records stamped with `taxonomy_version = "1.0.0"` remain fully valid without requiring immediate database reclassification.

## 3. Deprecation Lifecycle

When an identifier is scheduled for removal:
1. Mark the identifier as deprecated in `TaxonomyVersionManager`.
2. Record `deprecated_in`, `effective_sunset`, and `replacement_id`.
3. Reject assigning deprecated IDs to *new* incoming products.
4. Run a batch migration job to reclassify historical products to `replacement_id`.
5. Drop the identifier only when incrementing `MAJOR`.
