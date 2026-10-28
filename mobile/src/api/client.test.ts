import { api, ApiError } from "./client";
import { getAccessToken, getDevToken } from "../lib/token";
import { supabase } from "../lib/supabase";

jest.mock("../lib/token", () => ({
  getAccessToken: jest.fn(),
  getDevToken: jest.fn(),
}));

jest.mock("../lib/supabase", () => ({
  supabase: {
    auth: {
      refreshSession: jest.fn(),
      signOut: jest.fn(),
    },
  },
}));

const mockedGetAccessToken = jest.mocked(getAccessToken);
const mockedGetDevToken = jest.mocked(getDevToken);
const mockedRefreshSession = jest.mocked(supabase.auth.refreshSession);
const mockedSignOut = jest.mocked(supabase.auth.signOut);

function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  });
}

describe("api client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
    mockedGetAccessToken.mockResolvedValue("test-access-token");
    mockedGetDevToken.mockReturnValue(null);
    globalThis.fetch = jest.fn();
  });

  afterAll(() => {
    globalThis.fetch = originalFetch;
  });

  it("sends the access token and parses a JSON response", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ user_id: "user-123" }),
    );

    const result = await api<{ user_id: string }>("/me");

    expect(result.user_id).toBe("user-123");
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const [, request] = (globalThis.fetch as jest.Mock).mock.calls[0];
    expect(request.headers.get("Authorization")).toBe("Bearer test-access-token");
    expect(request.headers.get("Accept")).toBe("application/json");
  });

  it("returns undefined for HTTP 204", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      new Response(null, { status: 204 }),
    );

    await expect(api<void>("/example")).resolves.toBeUndefined();
  });

  it("normalizes a structured HTTP error", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      jsonResponse(
        {
          code: "catalog_unavailable",
          detail: "Catalog is temporarily unavailable.",
          request_id: "req-123",
        },
        503,
      ),
    );

    try {
      await api("/feed");
      throw new Error("Expected request to fail");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect(error).toMatchObject({
        status: 503,
        code: "catalog_unavailable",
        detail: "Catalog is temporarily unavailable.",
        requestId: "req-123",
        kind: "http",
      });
      expect((error as ApiError).isRetryable).toBe(true);
    }
  });

  it("does not refresh or retry an unauthorized developer token", async () => {
    mockedGetDevToken.mockReturnValue("dev-token");
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      jsonResponse({ detail: "Unauthorized" }, 401),
    );

    await expect(api("/me")).rejects.toMatchObject({
      status: 401,
    });
    expect(mockedRefreshSession).not.toHaveBeenCalled();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("rejects invalid API paths before making a request", async () => {
    await expect(api("https://example.com/me")).rejects.toMatchObject({
      code: "invalid_api_path",
    });
    await expect(api("//example.com/me")).rejects.toMatchObject({
      code: "invalid_api_path",
    });
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("converts network failures into a stable error", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue(
      new TypeError("Failed to fetch"),
    );

    await expect(api("/feed")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
      kind: "network",
    });
  });

  it("converts request timeout into a timeout error", async () => {
    const timeoutError = new Error("The operation was aborted");
    timeoutError.name = "AbortError";
    (globalThis.fetch as jest.Mock).mockRejectedValue(timeoutError);

    await expect(api("/feed", { timeoutMs: 100 })).rejects.toMatchObject({
      status: 0,
      code: "request_timeout",
      kind: "timeout",
    });
  });

  it("refreshes session and retries once for safe GET on 401", async () => {
    mockedRefreshSession.mockResolvedValue({
      data: {
        session: {
          access_token: "refreshed-token",
        } as any,
        user: null,
      },
      error: null,
    });

    (globalThis.fetch as jest.Mock)
      .mockResolvedValueOnce(jsonResponse({ detail: "Token expired" }, 401))
      .mockResolvedValueOnce(jsonResponse({ user_id: "user-refreshed" }, 200));

    const result = await api<{ user_id: string }>("/me");

    expect(result.user_id).toBe("user-refreshed");
    expect(mockedRefreshSession).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);

    const [, retryRequest] = (globalThis.fetch as jest.Mock).mock.calls[1];
    expect(retryRequest.headers.get("Authorization")).toBe("Bearer refreshed-token");
  });

  it("signs out and throws unauthorized error when refresh fails", async () => {
    mockedRefreshSession.mockResolvedValue({
      data: { session: null, user: null },
      error: new Error("Refresh token invalid") as any,
    });

    (globalThis.fetch as jest.Mock).mockResolvedValueOnce(
      jsonResponse({ detail: "Token expired" }, 401),
    );

    await expect(api("/me")).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
    });

    expect(mockedRefreshSession).toHaveBeenCalledTimes(1);
    expect(mockedSignOut).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("does not retry unsafe POST without idempotency key on 401", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValueOnce(
      jsonResponse({ detail: "Unauthorized" }, 401),
    );

    await expect(
      api("/wardrobe/items", {
        method: "POST",
        body: JSON.stringify({ item_id: "item-1" }),
      }),
    ).rejects.toMatchObject({
      status: 401,
    });

    expect(mockedRefreshSession).not.toHaveBeenCalled();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("retries idempotent POST on 401 when idempotencyKey is supplied", async () => {
    mockedRefreshSession.mockResolvedValue({
      data: {
        session: { access_token: "refreshed-token" } as any,
        user: null,
      },
      error: null,
    });

    (globalThis.fetch as jest.Mock)
      .mockResolvedValueOnce(jsonResponse({ detail: "Unauthorized" }, 401))
      .mockResolvedValueOnce(jsonResponse({ success: true }, 200));

    const result = await api<{ success: boolean }>("/wardrobe/items", {
      method: "POST",
      body: JSON.stringify({ item_id: "item-1" }),
      idempotencyKey: "idem-key-123",
    });

    expect(result.success).toBe(true);
    expect(mockedRefreshSession).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("handles malformed non-JSON response on 200 with invalid_response error", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue(
      new Response("Not valid json", {
        status: 200,
        headers: { "Content-Type": "text/html" },
      }),
    );

    await expect(api("/feed")).rejects.toMatchObject({
      status: 200,
      code: "invalid_response",
      kind: "invalid_response",
    });
  });
});
