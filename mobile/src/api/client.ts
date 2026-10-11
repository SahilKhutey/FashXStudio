import { supabase } from "../lib/supabase";
import { env } from "../lib/env";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public detail: string,
    public requestId?: string
  ) {
    super(`${code}: ${detail}`);
    this.name = "ApiError";
  }
}

async function parse(res: Response) {
  if (res.ok) {
    return res.status === 204 ? null : res.json();
  }
  let body: any = {};
  try {
    body = await res.json();
  } catch {
    // Non-JSON or empty response body
  }
  // RFC-7807 envelope from the backend: title or error code, detail, request_id
  throw new ApiError(
    res.status,
    body.title ?? body.code ?? "error",
    body.detail ?? "",
    body.request_id
  );
}

export async function api<T>(
  path: string,
  init: RequestInit & { idempotencyKey?: string; timeoutMs?: number } = {}
): Promise<T> {
  const attempt = async (token?: string) => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), init.timeoutMs ?? 20000);
    try {
      return await fetch(`${env.apiUrl}/api/v1${path}`, {
        ...init,
        signal: ctrl.signal,
        headers: {
          Accept: "application/json",
          ...(init.body && !(init.body instanceof FormData)
            ? { "Content-Type": "application/json" }
            : {}),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(init.idempotencyKey ? { "Idempotency-Key": init.idempotencyKey } : {}),
          ...init.headers,
        },
      });
    } finally {
      clearTimeout(timer);
    }
  };

  let {
    data: { session },
  } = await supabase.auth.getSession();

  let res = await attempt(session?.access_token);

  if (res.status === 401) {
    // Refresh session once, then retry once
    const { data } = await supabase.auth.refreshSession();
    if (!data.session) {
      await supabase.auth.signOut();
      throw new ApiError(401, "unauthorized", "Session expired");
    }
    res = await attempt(data.session.access_token);
  }

  return parse(res) as Promise<T>;
}

export const apiClient = api;
