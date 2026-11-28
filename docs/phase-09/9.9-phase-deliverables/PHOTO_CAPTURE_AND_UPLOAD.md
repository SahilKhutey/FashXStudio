# Photo Capture and Upload

- **Just-in-Time Permissions**: `mobile/src/features/tryon/permissions.ts` and `mobile/src/features/camera/permissionPolicy.ts` request camera or photo-library access only when the shopper initiates capture or gallery selection, with a settings deep-link fallback on denial.
- **Guidance & Validation**: `PhotoInstructions.tsx`, `GalleryPicker.tsx`, and `imageValidation.ts` enforce JPEG/PNG/WebP format, size limits, and explicit user review in `PhotoPreview.tsx` before upload.
- **Upload Flow**: Uses backend upload-intent media endpoints (`/api/v1/media/*`) rather than embedding a second upload engine.
- **Verification**: `mobile/src/features/tryon/__tests__/phase09_6_vto.test.tsx` and `mobile/__tests__/phase09_8_quality_a11y.test.tsx` pass in Jest; physical device camera lifecycle (`NOT_TESTED`) requires real hardware.
