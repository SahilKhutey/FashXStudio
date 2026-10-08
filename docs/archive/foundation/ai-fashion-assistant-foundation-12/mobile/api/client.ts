const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEV_USER_ID = process.env.EXPO_PUBLIC_DEV_USER_ID;

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  if (__DEV__ && DEV_USER_ID) {
    headers.set("X-User-ID", DEV_USER_ID);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let payload: { error?: { message?: string; code?: string } } = {};
    try {
      payload = await response.json();
    } catch {
      // Keep transport errors useful even if the server returned non-JSON.
    }
    throw new ApiError(
      response.status,
      payload.error?.message ?? `Request failed with status ${response.status}`,
      payload.error?.code,
    );
  }

  return (await response.json()) as T;
}
