/**
 * User-facing error message mapping for RFC-7807 error codes.
 * Raw error details and request IDs should be logged, not directly shown to end users.
 */

export const ERROR_MESSAGES: Record<string, string> = {
  // Authentication & session
  unauthorized: "Your session has expired. Please sign in again.",
  forbidden: "You do not have permission to access this resource.",
  not_found: "The requested item could not be found.",

  // Try-on & garment errors from Phase 5
  bad_input: "Invalid photo or garment input. Please try a different photo.",
  unsupported_garment: "This garment category or silhouette is currently not supported for virtual try-on.",
  rate_limited: "Daily virtual try-on limit reached. Please try again tomorrow.",
  provider_unavailable: "Virtual try-on service is temporarily busy. Please retry in a few moments.",
  tryon_failed: "Could not generate try-on result. Please try another photo or outfit.",
  budget_exceeded: "Virtual try-on capacity reached for today. Please try again tomorrow.",

  // Catalog & network
  network_error: "Unable to connect to the server. Please check your internet connection.",
  validation_error: "Please check your inputs and try again.",

  // Catch-all
  generic: "Something unexpected happened. Please try again later.",
};

export function getErrorMessage(code: string, requestId?: string): string {
  if (requestId) {
    console.warn(`[ApiError] code: ${code}, requestId: ${requestId}`);
  }
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.generic || "An unexpected error occurred.";
}
