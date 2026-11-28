# Product Image Policy

- `ProductGallery` (`mobile/src/features/product-detail/components/ProductGallery.tsx`) renders authorized `ProductImage[]` sorted by `position`, shows `"1 / N"` counter, and falls back to `"Product image unavailable"` when empty.
- Display permission (`display_allowed`) is distinct from VTO permission (`vto_allowed`).
