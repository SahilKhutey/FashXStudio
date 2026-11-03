/**
 * Safe redirect validator for external retailer shopping links (RC-03 / Rule I12).
 *
 * Enforces:
 * - Valid URL string
 * - HTTPS protocol strictly required (no http, javascript, file, data, etc.)
 * - Non-empty hostname
 * - No userinfo / embedded credentials (user:pass@host)
 * - Hostname domain matching against optional allowed hosts
 */

export function isSafeRetailerRedirect(
  urlString: string | null | undefined,
  allowedHosts?: readonly string[]
): boolean {
  if (!urlString || typeof urlString !== "string") {
    return false;
  }

  try {
    const trimmed = urlString.trim();
    const url = new URL(trimmed);

    // Protocol must strictly be https:
    if (url.protocol !== "https:") {
      return false;
    }

    // Hostname must be non-empty
    if (!url.hostname || url.hostname.trim() === "") {
      return false;
    }

    // Reject embedded credentials (e.g. https://user:pass@evil.com)
    if (url.username || url.password) {
      return false;
    }

    // Reject whitespace in hostname
    if (/\s/.test(url.hostname)) {
      return false;
    }

    // If allowed hosts list is provided, verify match
    if (allowedHosts && allowedHosts.length > 0) {
      const host = url.hostname.toLowerCase();
      const matched = allowedHosts.some(
        (allowed) => host === allowed.toLowerCase() || host.endsWith(`.${allowed.toLowerCase()}`)
      );
      if (!matched) {
        return false;
      }
    }

    return true;
  } catch {
    return false;
  }
}

export function assertSafeRetailerRedirect(
  urlString: string | null | undefined,
  allowedHosts?: readonly string[]
): string {
  if (!isSafeRetailerRedirect(urlString, allowedHosts)) {
    throw new Error(`Unsafe retailer redirect URL rejected: ${urlString}`);
  }
  return urlString!.trim();
}
