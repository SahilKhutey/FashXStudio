import { authProviderService } from "./auth.instance";
import type { AuthSession } from "./auth.types";

let refreshPromise: Promise<AuthSession> | null = null;

/**
 * Single-flight session refresh manager so concurrent 401 responses
 * trigger at most one identity-provider refresh operation.
 */
export function refreshSessionOnce(): Promise<AuthSession> {
  if (!refreshPromise) {
    refreshPromise = authProviderService.refreshSession().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}
