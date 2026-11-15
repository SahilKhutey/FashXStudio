/**
 * Secure Token Persistence Adapter using Expo SecureStore.
 * Ensures access and refresh tokens are stored encrypted in Keychain (iOS) / KeyStore (Android).
 */

import * as SecureStore from "expo-secure-store";

const ACCESS_TOKEN_KEY = "fashx_auth_access_token";
const REFRESH_TOKEN_KEY = "fashx_auth_refresh_token";
const ID_TOKEN_KEY = "fashx_auth_id_token";
const SUB_KEY = "fashx_auth_cognito_sub";

export async function saveAuthTokens(
  accessToken: string,
  idToken: string,
  refreshToken?: string,
  sub?: string,
): Promise<void> {
  const promises: Promise<void>[] = [
    SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken),
    SecureStore.setItemAsync(ID_TOKEN_KEY, idToken),
  ];

  if (refreshToken) {
    promises.push(SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken));
  }
  if (sub) {
    promises.push(SecureStore.setItemAsync(SUB_KEY, sub));
  }

  await Promise.all(promises);
}

export async function getPersistedAccessToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getPersistedRefreshToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function getPersistedIdToken(): Promise<string | null> {
  return await SecureStore.getItemAsync(ID_TOKEN_KEY);
}

export async function getPersistedCognitoSub(): Promise<string | null> {
  return await SecureStore.getItemAsync(SUB_KEY);
}

export async function clearAuthTokens(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY),
    SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY),
    SecureStore.deleteItemAsync(ID_TOKEN_KEY),
    SecureStore.deleteItemAsync(SUB_KEY),
  ]);
}
