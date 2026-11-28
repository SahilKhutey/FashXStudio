# Saved Look Data Model

- `CreateSavedLookRequest` (`title` 1–100 non-blank chars, optional `description` up to 1000 chars, `item_ids` 1–30 UUIDs).
- `SavedLookSummary` stores `id`, `user_id`, `title`, `description`, deduplicated `item_ids`, `item_count`, `created_at`, `updated_at`.
