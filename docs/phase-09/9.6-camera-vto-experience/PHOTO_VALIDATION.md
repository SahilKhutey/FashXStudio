# Photo Validation

- `validateLocalImage()` (`mobile/src/features/tryon/imageValidation.ts`) checks file existence, non-zero byte size, and `TRYON_IMAGE_POLICY.maxFileSizeBytes` (`10 MB`) prior to preview.
- Backend `backend/fashx/tryon/validation/` remains authoritative for byte inspection, dimensions, decompression bombs, and person/garment checks.
