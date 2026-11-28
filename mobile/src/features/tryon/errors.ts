const TRYON_ERROR_MESSAGES: Record<string, string> = {
  VTO_CONSENT_REQUIRED:
    "Please grant third-party Virtual Try-On consent before submitting.",
  IMAGE_NOT_OWNED_OR_NOT_FOUND:
    "This photo could not be found. Please choose another photo.",
  IMAGE_NOT_READY:
    "Your photo is still being validated. Please wait a moment.",
  IMAGE_FORMAT_UNSUPPORTED:
    "Please use a JPEG, PNG, or WebP image.",
  IMAGE_TOO_LARGE:
    "This photo is too large. Please choose a smaller image.",
  PERSON_NOT_DETECTED:
    "We couldn't identify a suitable person in this photo. Please try a clearer photo.",
  PRODUCT_NOT_ACTIVE:
    "This item is no longer available for virtual try-on.",
  GARMENT_PROCESSING_NOT_AUTHORIZED:
    "Virtual try-on is not permitted for this product image.",
  UNSUPPORTED_GARMENT_CATEGORY:
    "Virtual try-on is not available for this garment category yet.",
  VTO_RATE_LIMITED:
    "You have reached the virtual try-on limit. Please try again later.",
  VTO_SERVICE_UNAVAILABLE:
    "Virtual try-on is temporarily busy. Please try again shortly.",
  IDEMPOTENCY_CONFLICT:
    "A conflicting try-on request is already in progress.",
  TRYON_JOB_NOT_FOUND:
    "This try-on job could not be found.",
  TRYON_RESULT_NOT_READY:
    "Your try-on result is still being prepared.",
  TRYON_RESULT_EXPIRED:
    "This virtual try-on result has expired.",
  SUBMISSION_UNKNOWN:
    "We're checking the status of your request. Please wait before retrying.",
};

export function mapTryOnErrorCode(code?: string | null): string {
  if (!code) {
    return "Try-on could not be completed. Please try again.";
  }
  return (
    TRYON_ERROR_MESSAGES[code] ??
    "Try-on could not be completed. Please try again."
  );
}
