# 12 — Database Schema and Migration

## 1. Migration Specification

- **Migration ID**: `0056_add_product_size_data_and_revisions`
- **Revises**: `0055_add_vto_fit_separation_and_size_charts`
- **File**: `database/migrations/versions/0056_add_product_size_data_and_revisions.py`

## 2. Tables Created

| Table Name | Description | Key Constraints & Indexes |
|---|---|---|
| `size_system_definitions` | Regional and merchant sizing system registry | Unique `code`, Index `merchant_id` |
| `measurement_field_definitions` | Standard garment measurement taxonomy | Unique `code` |
| `product_size_charts` | Top-level container linking to merchant product | Unique `merchant_product_id`, FK `merchants.id` |
| `size_chart_revisions` | Immutable versioned size chart revisions | Unique (`chart_id`, `version`), Index `content_fingerprint` |
| `size_chart_rows` | Size label rows within a revision | Unique (`revision_id`, `merchant_size`) |
| `size_chart_measurements` | Granular linear measurements | Unique (`row_id`, `field_code`), FK `size_chart_rows.id` |
| `inventory_snapshots` | Point-in-time variant availability | Indexes on `variant_id`, `merchant_product_id`, `observed_at` |
| `size_chart_events` | Audit trail for version and lifecycle transitions | Indexes on `merchant_product_id`, `chart_id`, `created_at` |
| `size_chart_quarantine` | Quarantine store for invalid submissions | Indexes on `merchant_product_id`, `merchant_id`, `review_status` |

## 3. Rollback Procedure
The downgrade function drops all 9 tables in reverse dependency order:
```python
def downgrade() -> None:
    op.drop_table("size_chart_quarantine")
    op.drop_table("size_chart_events")
    op.drop_table("inventory_snapshots")
    op.drop_table("size_chart_measurements")
    op.drop_table("size_chart_rows")
    op.drop_table("size_chart_revisions")
    op.drop_table("product_size_charts")
    op.drop_table("measurement_field_definitions")
    op.drop_table("size_system_definitions")
```
