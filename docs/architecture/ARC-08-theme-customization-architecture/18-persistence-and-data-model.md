# ARC-08: 18 — Persistence and Data Model

## 1. Relational Tables (PostgreSQL JSONB)
1. `theme_definitions`: Platform theme definitions (`id`, `version`, `tokens`, `supported_layouts`).
2. `layout_definitions`: Layout presets and slot definitions (`id`, `version`, `supported_slots`, `default_settings`).
3. `component_definitions`: Approved component metadata and property schemas (`id`, `version`, `property_schema`).
4. `menu_customizations`: Active draft customization per menu (`organization_id`, `menu_id`, `revision`, `configuration`).
5. `customization_revisions`: Immutable revision history (`customization_id`, `revision`, `configuration`).
6. `configuration_migrations`: Schema version upgrade ledger (`source_version`, `target_version`, `applied_at`).

## 2. Multi-Tenancy & Row-Level Security
Tables enforce composite tenant ownership (`organization_id`, `menu_id`). PostgreSQL RLS guarantees that queries cannot access another organization's customization drafts.
