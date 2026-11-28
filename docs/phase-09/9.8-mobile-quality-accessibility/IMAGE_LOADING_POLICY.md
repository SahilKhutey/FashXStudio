# Image Loading Policy

- `ImageWithFallback` (`mobile/src/components/ImageWithFallback.tsx`) uses `expo-image` (`cachePolicy="memory-disk"`) and switches to an accessible `"Image unavailable"` fallback on null or failed URIs without retry loops.
