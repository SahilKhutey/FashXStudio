/**
 * Authenticated Fetch Wrapper for FashXStudio Mobile.
 * Attaches the verified Amazon Cognito access token to API requests.
 */

import { getValidAccessToken } from "../session";

export async function authenticatedFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = await getValidAccessToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, {
    ...options,
    headers,
  });
}
