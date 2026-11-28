# 04 — Product Image Handling

- `mobile/src/features/catalog/components/ProductImage.tsx` renders `expo-image` with `contentFit="cover"`, preserves aspect ratio, and falls back to `"Image unavailable"` when `url` is null or image loading fails.
- `ProductSearchItemSchema` validates `primary_image_url` as a valid URL or `null`.
