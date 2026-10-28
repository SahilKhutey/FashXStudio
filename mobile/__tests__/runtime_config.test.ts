import { validateRuntimeConfig, RuntimeConfig } from "../src/lib/env";

describe("validateRuntimeConfig fail-closed release guard", () => {
  const validProdConfig: RuntimeConfig = {
    apiBaseUrl: "https://api.fashxstudio.com",
    allowDevAuth: false,
    supabaseUrl: "https://auth.fashxstudio.com",
    supabaseAnonKey: "anon-key-prod",
  };

  const devConfig: RuntimeConfig = {
    apiBaseUrl: "http://10.0.2.2:8000",
    allowDevAuth: true,
    supabaseUrl: "https://dummy-fashx.supabase.co",
    supabaseAnonKey: "dummy-anon-key",
  };

  it("passes valid production configuration with HTTPS and dev auth disabled", () => {
    const result = validateRuntimeConfig(validProdConfig, true);
    expect(result.apiBaseUrl).toBe("https://api.fashxstudio.com");
    expect(result.allowDevAuth).toBe(false);
  });

  it("allows non-HTTPS and dev auth when isProduction is false", () => {
    const result = validateRuntimeConfig(devConfig, false);
    expect(result.apiBaseUrl).toBe("http://10.0.2.2:8000");
    expect(result.allowDevAuth).toBe(true);
  });

  it("fails closed if production API uses non-HTTPS scheme", () => {
    const insecureProdConfig: RuntimeConfig = {
      ...validProdConfig,
      apiBaseUrl: "http://api.fashxstudio.com",
    };
    expect(() => validateRuntimeConfig(insecureProdConfig, true)).toThrow(
      "Production API must use HTTPS"
    );
  });

  it("fails closed if production allows dev auth tokens", () => {
    const devAuthProdConfig: RuntimeConfig = {
      ...validProdConfig,
      allowDevAuth: true,
    };
    expect(() => validateRuntimeConfig(devAuthProdConfig, true)).toThrow(
      "Development authentication is disabled in production"
    );
  });

  it("fails closed if production violates both HTTPS and dev auth", () => {
    const invalidProdConfig: RuntimeConfig = {
      apiBaseUrl: "http://localhost:8000",
      allowDevAuth: true,
    };
    expect(() => validateRuntimeConfig(invalidProdConfig, true)).toThrow();
  });
});
