export const TRYON_IMAGE_POLICY = {
  maxFileSizeBytes: 10 * 1024 * 1024,
  maxWidth: 4096,
  maxHeight: 4096,
  maxPixels: 20_000_000,
  supportedMimeTypes: ["image/jpeg", "image/png", "image/webp"] as const,
};

export const TRYON_POLL_INTERVAL_MS = 2500;
export const TRYON_MAX_POLL_INTERVAL_MS = 10_000;

export const TRYON_DISCLAIMER =
  "This is an AI-generated visual representation. It does not verify garment size, measurements, comfort, stretch, drape or physical fit.";
