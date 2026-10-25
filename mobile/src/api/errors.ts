export type ApiErrorKind =
  | "http"
  | "network"
  | "timeout"
  | "invalid_response";

export class ApiError extends Error {
  override readonly name = "ApiError";

  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly detail: string,
    public readonly requestId?: string,
    public readonly kind: ApiErrorKind = "http",
  ) {
    super(`${code}: ${detail}`);
    Object.setPrototypeOf(this, new.target.prototype);
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }

  get isRetryable(): boolean {
    return (
      this.kind === "network" ||
      this.kind === "timeout" ||
      this.status === 408 ||
      this.status === 429 ||
      this.status >= 500
    );
  }
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (
    error instanceof Error &&
    (error.name === "AbortError" || error.name === "TimeoutError")
  ) {
    return new ApiError(
      0,
      "request_timeout",
      "The request took too long. Please try again.",
      undefined,
      "timeout",
    );
  }

  return new ApiError(
    0,
    "network_error",
    "Could not reach the server. Check your connection and try again.",
    undefined,
    "network",
  );
}
