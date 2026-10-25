import { supabase } from "../lib/supabase";
import { env } from "../lib/env";
import { getAccessToken, getDevToken } from "../lib/token";
import { ApiError, toApiError } from "./errors";

export { ApiError } from "./errors";

export type ApiRequestInit = RequestInit & {
  idempotencyKey?: string;
  timeoutMs?: number;
};

type ErrorPayload = {
  title?: unknown;
  code?: unknown;
  detail?: unknown;
  request_id?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function asNonEmptyString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function getRequestId(
  response: Response,
  payload: ErrorPayload,
): string | undefined {
  return (
    asNonEmptyString(payload.request_id) ??
    response.headers.get("x-request-id") ??
    response.headers.get("x-correlation-id") ??
    undefined
  );
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json") || contentType.includes("+json");

  let payload: unknown;
  try {
    payload = isJson ? await response.json() : await response.text();
  } catch {
    if (response.ok) {
      throw new ApiError(
        response.status,
        "invalid_response",
        "The server returned an unreadable response.",
        response.headers.get("x-request-id") ?? undefined,
        "invalid_response",
      );
    }
    payload = undefined;
  }

  if (response.ok) {
    if (isJson || payload === undefined || payload === "") {
      return payload as T;
    }

    throw new ApiError(
      response.status,
      "invalid_response",
      "Expected a JSON response from the server.",
      response.headers.get("x-request-id") ?? undefined,
      "invalid_response",
    );
  }

  const body: ErrorPayload = isRecord(payload) ? (payload as ErrorPayload) : {};
  const detail =
    asNonEmptyString(body.detail) ??
    (typeof payload === "string" && payload.trim() ? payload : "The request could not be completed.");

  throw new ApiError(
    response.status,
    asNonEmptyString(body.code) ?? asNonEmptyString(body.title) ?? "api_error",
    detail,
    getRequestId(response, body),
    "http",
  );
}

function makeUrl(path: string): string {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new ApiError(
      0,
      "invalid_api_path",
      "API requests must use a relative path beginning with '/'.",
      undefined,
      "invalid_response",
    );
  }

  const base = env.apiUrl.replace(/\/+$/, "");
  return `${base}/api/v1${path}`;
}

async function requestOnce<T>(
  url: string,
  init: ApiRequestInit,
  token?: string,
): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = init.timeoutMs ?? 20_000;
  let timedOut = false;

  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");

    const hasBody = init.body !== undefined && init.body !== null;
    const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;

    if (hasBody && !isFormData && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (init.idempotencyKey) {
      headers.set("Idempotency-Key", init.idempotencyKey);
    }

    const response = await fetch(url, {
      ...init,
      headers,
      signal: controller.signal,
    });

    return await parseResponse<T>(response);
  } catch (error) {
    if (timedOut) {
      throw new ApiError(
        0,
        "request_timeout",
        "The request took too long. Please try again.",
        undefined,
        "timeout",
      );
    }

    if (error instanceof ApiError) throw error;
    throw toApiError(error);
  } finally {
    clearTimeout(timer);
  }
}

export async function api<T>(
  path: string,
  init: ApiRequestInit = {},
): Promise<T> {
  const url = makeUrl(path);
  const token = await getAccessToken();

  try {
    return await requestOnce<T>(url, init, token);
  } catch (error) {
    const apiError = toApiError(error);

    // Refresh once for an expired Supabase session.
    // Do not retry developer tokens or arbitrary non-idempotent requests.
    const method = (init.method ?? "GET").toUpperCase();
    const isSafeToRepeat = method === "GET" || method === "HEAD" || Boolean(init.idempotencyKey);

    if (
      apiError.status !== 401 ||
      getDevToken() ||
      !isSafeToRepeat
    ) {
      throw apiError;
    }

    const { data, error: refreshError } = await supabase.auth.refreshSession();
    if (refreshError || !data.session) {
      await supabase.auth.signOut();
      throw new ApiError(
        401,
        "unauthorized",
        "Your session has expired. Please sign in again.",
      );
    }

    // One retry only. A second 401 is returned to the caller.
    return requestOnce<T>(
      url,
      init,
      data.session.access_token,
    );
  }
}

export const apiClient = api;
