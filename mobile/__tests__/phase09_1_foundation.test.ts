import * as SecureStore from "expo-secure-store";
import { parseEnvironment } from "../src/config/environment";
import { useAppStore } from "../src/stores/app.store";
import { ProductSummarySchema } from "../src/api/schemas/product.schema";
import { toPermissionState } from "../src/services/camera.service";
import {
  saveAuthTokens,
  getPersistedAccessToken,
  getPersistedRefreshToken,
  clearAuthTokens,
} from "../src/auth/secureStorage";

jest.mock("expo-camera", () => ({
  Camera: {},
  CameraView: "CameraView",
  useCameraPermissions: jest.fn(),
}));

describe("Phase 09.1 environment configuration (MOB-ENV)", () => {
  it("parses valid development configuration", () => {
    const cfg = parseEnvironment({
      APP_ENV: "development",
      EXPO_PUBLIC_APP_ENV: "development",
      EXPO_PUBLIC_API_BASE_URL: "http://10.0.2.2:8000",
      EXPO_PUBLIC_ENABLE_DEV_TOOLS: "true",
    });
    expect(cfg.appEnv).toBe("development");
    expect(cfg.apiBaseUrl).toBe("http://10.0.2.2:8000");
    expect(cfg.enableDevTools).toBe(true);
  });

  it("rejects unknown APP_ENV", () => {
    expect(() =>
      parseEnvironment({
        APP_ENV: "qa",
        EXPO_PUBLIC_API_BASE_URL: "https://qa.fashxstudio.com",
      }),
    ).toThrow("Invalid application environment configuration");
  });

  it("rejects mismatched APP_ENV and EXPO_PUBLIC_APP_ENV", () => {
    expect(() =>
      parseEnvironment({
        APP_ENV: "staging",
        EXPO_PUBLIC_APP_ENV: "production",
        EXPO_PUBLIC_API_BASE_URL: "https://staging-api.fashxstudio.com",
      }),
    ).toThrow("Application environment mismatch");
  });

  it("rejects HTTP API URL in staging and production", () => {
    expect(() =>
      parseEnvironment({
        APP_ENV: "production",
        EXPO_PUBLIC_APP_ENV: "production",
        EXPO_PUBLIC_API_BASE_URL: "http://api.fashxstudio.com",
      }),
    ).toThrow("production API must use HTTPS");

    expect(() =>
      parseEnvironment({
        APP_ENV: "staging",
        EXPO_PUBLIC_APP_ENV: "staging",
        EXPO_PUBLIC_API_BASE_URL: "http://staging-api.fashxstudio.com",
      }),
    ).toThrow("staging API must use HTTPS");
  });

  it("forces dev tools disabled in production", () => {
    const cfg = parseEnvironment({
      APP_ENV: "production",
      EXPO_PUBLIC_APP_ENV: "production",
      EXPO_PUBLIC_API_BASE_URL: "https://api.fashxstudio.com",
      EXPO_PUBLIC_ENABLE_DEV_TOOLS: "true",
    });
    expect(cfg.enableDevTools).toBe(false);
  });
});

describe("Phase 09.1 app UI store (MOB-STATE)", () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it("updates category, searchQuery, selectedColors and resets cleanly", () => {
    useAppStore.getState().setSelectedCategory("shirts");
    useAppStore.getState().setSearchQuery("black kurta");
    useAppStore.getState().setSelectedColors(["black", "navy"]);

    expect(useAppStore.getState().selectedCategory).toBe("shirts");
    expect(useAppStore.getState().searchQuery).toBe("black kurta");
    expect(useAppStore.getState().selectedColors).toEqual(["black", "navy"]);

    useAppStore.getState().reset();
    expect(useAppStore.getState().selectedCategory).toBeNull();
    expect(useAppStore.getState().searchQuery).toBe("");
    expect(useAppStore.getState().selectedColors).toEqual([]);
  });
});

describe("Phase 09.1 API schema validation (MOB-API)", () => {
  it("validates a well-formed product summary and rejects malformed payloads", () => {
    const valid = ProductSummarySchema.parse({
      id: "11111111-1111-4111-8111-111111111111",
      title: "Minimal Cotton Tee",
      category: "tshirts",
      price: 799,
      currency: "INR",
      availability: "IN_STOCK",
      imageUrl: "https://cdn.fashxstudio.com/products/1.jpg",
    });
    expect(valid.availability).toBe("IN_STOCK");

    expect(() =>
      ProductSummarySchema.parse({
        id: "not-a-uuid",
        title: "Invalid",
        category: "tshirts",
        price: -10,
        currency: "IN",
        availability: "IN_STOCK",
        imageUrl: null,
      }),
    ).toThrow();
  });
});

describe("Phase 09.1 camera permission states (MOB-PERM)", () => {
  it("maps expo-camera permission objects to PermissionState", () => {
    expect(toPermissionState(null)).toBe("UNKNOWN");
    expect(toPermissionState({ granted: true })).toBe("GRANTED");
    expect(toPermissionState({ granted: false, canAskAgain: true })).toBe("DENIED");
    expect(toPermissionState({ granted: false, canAskAgain: false })).toBe("BLOCKED");
  });
});

describe("Phase 09.1 secure token storage (AUTH-MOB)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("saves, reads, and clears tokens via SecureStore", async () => {
    const store: Record<string, string> = {};
    jest
      .spyOn(SecureStore, "setItemAsync")
      .mockImplementation(async (key, value) => {
        store[key] = value;
      });
    jest
      .spyOn(SecureStore, "getItemAsync")
      .mockImplementation(async (key) => store[key] ?? null);
    jest
      .spyOn(SecureStore, "deleteItemAsync")
      .mockImplementation(async (key) => {
        delete store[key];
      });

    await saveAuthTokens("acc-123", "id-456", "ref-789", "sub-1");
    expect(await getPersistedAccessToken()).toBe("acc-123");
    expect(await getPersistedRefreshToken()).toBe("ref-789");

    await clearAuthTokens();
    expect(await getPersistedAccessToken()).toBeNull();
    expect(await getPersistedRefreshToken()).toBeNull();
  });
});
