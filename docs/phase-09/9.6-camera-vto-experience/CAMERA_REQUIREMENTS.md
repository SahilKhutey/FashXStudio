# Camera Requirements

- Camera access is requested via `mobile/src/features/tryon/CameraCapture.tsx` only when the shopper chooses `Take a photo`, never on app launch.
- `GalleryPicker` (`mobile/src/features/tryon/components/GalleryPicker.tsx`) uses `expo-image-picker` with `exif: false`.
