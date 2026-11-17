/**
 * Session Management & Proactive Token Retrieval for FashXStudio Mobile.
 */

import { getPersistedAccessToken, clearAuthTokens } from "./secureStorage";
import { getDevToken } from "../lib/token";

let inMemoryAccessToken: string | null = null;

export function setInMemoryAccessToken(token: string | null): void {
  inMemoryAccessToken = token;
}

/**
 * Returns a valid access token for API requests.
 * Checks devToken override (if non-production), then in-memory cache, then SecureStore.
 */
export async function getValidAccessToken(): Promise<string | null> {
  // 1. Check development token override
  const devTok = getDevToken();
  if (devTok) {
    return devTok;
  }

  // 2. Check in-memory cached token
  if (inMemoryAccessToken) {
    return inMemoryAccessToken;
  }

  // 3. Fallback to persisted SecureStore
  const persisted = await getPersistedAccessToken();
  if (persisted) {
    inMemoryAccessToken = persisted;
    return persisted;
  }

  return null;
}

/**
 * Clears all active session state across memory and device keystore.
 */
export async function purgeLocalSession(): Promise<void> {
  inMemoryAccessToken = null;
  await clearAuthTokens();
}
