import { compareVersions } from "../src/lib/config";
import { getErrorMessage, ERROR_MESSAGES } from "../src/lib/errors";
import { ApiError } from "../src/api/client";

describe("Mobile Remote Config Version Comparison", () => {
  it("correctly identifies older versions", () => {
    expect(compareVersions("0.0.9", "0.1.0")).toBe(-1);
    expect(compareVersions("0.1.0", "0.1.1")).toBe(-1);
    expect(compareVersions("0.1.0", "1.0.0")).toBe(-1);
  });

  it("correctly identifies equal versions", () => {
    expect(compareVersions("0.1.0", "0.1.0")).toBe(0);
    expect(compareVersions("1.2.3", "1.2.3")).toBe(0);
  });

  it("correctly identifies newer versions", () => {
    expect(compareVersions("0.1.1", "0.1.0")).toBe(1);
    expect(compareVersions("1.0.0", "0.9.9")).toBe(1);
  });
});

describe("Error Mapping Table (RFC-7807)", () => {
  it("maps try-on codes from Phase 5 to user-safe copy", () => {
    expect(getErrorMessage("bad_input")).toBe(ERROR_MESSAGES.bad_input);
    expect(getErrorMessage("unsupported_garment")).toBe(ERROR_MESSAGES.unsupported_garment);
    expect(getErrorMessage("rate_limited")).toBe(ERROR_MESSAGES.rate_limited);
    expect(getErrorMessage("provider_unavailable")).toBe(ERROR_MESSAGES.provider_unavailable);
  });

  it("maps session and authorization errors", () => {
    expect(getErrorMessage("unauthorized")).toBe(ERROR_MESSAGES.unauthorized);
    expect(getErrorMessage("forbidden")).toBe(ERROR_MESSAGES.forbidden);
  });

  it("falls back to generic user message for unmapped codes", () => {
    expect(getErrorMessage("unknown_error_code")).toBe(ERROR_MESSAGES.generic);
  });
});

describe("ApiError Envelope", () => {
  it("encapsulates status, code, detail, and requestId", () => {
    const err = new ApiError(400, "bad_input", "Photo resolution too low", "req-1234");
    expect(err.status).toBe(400);
    expect(err.code).toBe("bad_input");
    expect(err.detail).toBe("Photo resolution too low");
    expect(err.requestId).toBe("req-1234");
    expect(err.message).toBe("bad_input: Photo resolution too low");
  });
});
