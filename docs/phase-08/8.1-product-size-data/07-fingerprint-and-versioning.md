# 07 — Fingerprinting and Versioning

## 1. Canonical Fingerprinting

To prevent spurious revision churn caused by feed re-fetches, FashXStudio computes a deterministic SHA-256 canonical fingerprint over normalized size data.

### Fields Included in Fingerprint
1. `size_system`: Code of the sizing system.
2. `measurement_basis`: `BODY` or `GARMENT`.
3. `default_unit`: Base measurement unit (`CM`, `INCH`).
4. `rows`:
   - `merchant_size`: Trimmed and uppercase.
   - `sort_order`: Int integer index.
   - `measurements`: Sorted alphabetically by `field_code`, with `normalized_cm` formatted as a fixed 2-decimal string (`"96.00"`).

### Fields Excluded from Fingerprint
- `retrieved_at` timestamps.
- Feed transaction IDs and batch headers.
- Transient sync metadata.

If a merchant feed runs every 6 hours and delivers identical dimensions, the fingerprint matches the active revision. The system logs a `NO_OP_UNCHANGED` event and does not increment the version number.

## 2. Version Progression & Immutability

When dimensions, labels, or unit conventions genuinely change:
1. `version` increments by 1 (`v1` $\rightarrow$ `v2`).
2. The previous revision's `is_current` is set to `false`.
3. The new revision is stored with `is_current = true`.
4. An audit event `VERSION_INCREMENTED` is recorded with change summary metrics in `size_chart_events`.
5. Previous revisions remain intact and accessible via `/products/{id}/size-chart/revisions`.
