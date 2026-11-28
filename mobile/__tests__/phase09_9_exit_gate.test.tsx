import { api } from "../src/api/client";
import { ProviderAuthService } from "../src/auth/auth.service";
import type { AuthProvider } from "../src/auth/auth.provider";
import { performAppLogout } from "../src/auth/logout";
import { parseEnvironment } from "../src/config/environment";
import { flattenSearchPages } from "../src/features/catalog/flatten-pages";
import { useOnboardingStore } from "../src/features/onboarding/onboarding.store";
import {
  completeOnboarding,
  onboardingService,
} from "../src/features/onboarding/onboarding.service";
import {
  fetchProductDetail,
  requestMerchantRedirect,
} from "../src/features/product-detail/api";
import {
  availabilityMessage,
  canPurchase,
} from "../src/features/product-detail/utils/availability";
import { searchProducts } from "../src/features/search/search.api";
import { mapTryOnErrorCode } from "../src/features/tryon/errors";
import {
  cancelTryOnJob,
  getTryOnJob,
  submitTryOnJob,
} from "../src/features/tryon/tryonApi";
import { createSavedLook, deleteSavedLook } from "../src/features/wardrobe/api";
import { wardrobeKeys } from "../src/features/wardrobe/hooks";
import { captureSafeError } from "../src/services/crashReporting";

jest.mock("../src/api/client", () => {
  const actual = jest.requireActual("../src/api/client");
  return {
    ...actual,
    api: jest.fn(),
  };
});

jest.mock("../src/auth/auth.instance", () => ({
  authService: {
    getCurrentSession: jest.fn().mockResolvedValue(null),
    getAccessToken: jest.fn().mockResolvedValue(null),
    refreshSession: jest.fn().mockResolvedValue(null),
    logout: jest.fn().mockResolvedValue(undefined),
  },
}));

const mockedApi = api as jest.MockedFunction<typeof api>;

describe("Phase 09.9 — End-to-End Mobile Exit Gate", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useOnboardingStore.getState().reset();
  });

  it("enforces HTTPS in staging and production environments", () => {
    expect(() =>
      parseEnvironment({
        APP_ENV: "production",
        EXPO_PUBLIC_API_BASE_URL: "http://api.fashx.example.com",
      }),
    ).toThrow("production API must use HTTPS");

    const staging = parseEnvironment({
      APP_ENV: "staging",
      EXPO_PUBLIC_API_BASE_URL: "https://staging-api.fashx.example.com/",
    });
    expect(staging.appEnv).toBe("staging");
    expect(staging.apiBaseUrl).toBe("https://staging-api.fashx.example.com");
  });

  it("supports registration, verification, session refresh, and account-isolated logout", async () => {
    const provider: AuthProvider = {
      register: jest.fn().mockResolvedValue({
        status: "VERIFICATION_REQUIRED",
        email: "shopper@example.com",
        destination: "s***@example.com",
      }),
      login: jest.fn().mockResolvedValue({ status: "AUTHENTICATED" }),
      confirmRegistration: jest.fn().mockResolvedValue(undefined),
      resendVerificationCode: jest.fn().mockResolvedValue(undefined),
      startRecovery: jest.fn().mockResolvedValue(undefined),
      completeRecovery: jest.fn().mockResolvedValue(undefined),
      getCurrentSession: jest.fn().mockResolvedValue(null),
      getAccessToken: jest.fn().mockResolvedValue("tok-1"),
      refreshSession: jest.fn().mockResolvedValue({
        accessToken: "tok-2",
        expiresAt: Date.now() + 3600_000,
        user: { subject: "user-1", email: "shopper@example.com" },
      }),
      logout: jest.fn().mockResolvedValue(undefined),
    };

    const service = new ProviderAuthService(provider);
    const reg = await service.register({
      name: "Asha Rao",
      email: "shopper@example.com",
      password: "Password123!",
    });
    expect(reg.status).toBe("VERIFICATION_REQUIRED");

    await service.confirmRegistration({
      email: "shopper@example.com",
      code: "123456",
    });
    expect(provider.confirmRegistration).toHaveBeenCalledWith({
      email: "shopper@example.com",
      code: "123456",
    });

    const refreshed = await service.refreshSession();
    expect(refreshed?.accessToken).toBe("tok-2");

    await performAppLogout();
    expect(wardrobeKeys.items("user-1")).not.toEqual(wardrobeKeys.items("user-2"));
    expect(wardrobeKeys.looks("user-1")).not.toEqual(wardrobeKeys.looks("user-2"));
  });

  it("walks the golden shopper journey across onboarding, discovery, PDP, VTO, wardrobe, and redirect", async () => {
    // 1. Onboarding draft & persistence
    useOnboardingStore.getState().updateDraft({
      displayName: "Asha",
      heightCm: 168,
      stylePreferences: ["MINIMALIST"],
      colorPreferences: ["NAVY"],
      measurements: { CHEST: 88 },
    });
    mockedApi.mockResolvedValueOnce({ user_id: "user-1", display_name: "Asha" });
    mockedApi.mockResolvedValueOnce({ ok: true });
    await onboardingService.saveProfileDraft(useOnboardingStore.getState().draft);
    expect(mockedApi).toHaveBeenCalledWith(
      "/profile/me",
      expect.objectContaining({ method: "PATCH" }),
    );

    mockedApi.mockResolvedValueOnce({ user_id: "user-1", display_name: "Asha" });
    mockedApi.mockResolvedValueOnce({ ok: true });
    await completeOnboarding();
    expect(useOnboardingStore.getState().currentStep).toBe("WELCOME");

    // 2. Search discovery & multi-merchant deduplication
    mockedApi.mockResolvedValueOnce({
      search_id: "search-1",
      query: "linen blazer",
      items: [
        {
          product_id: "prod-1",
          merchant_product_id: "offer-a",
          title: "Navy Linen Blazer",
          brand: { id: "brand-1", name: "Studio" },
          price: { amount: 14900, currency: "USD" },
          availability: "IN_STOCK",
          matched_attributes: ["linen"],
          primary_image_url: "https://cdn.example.com/a.jpg",
        },
      ],
      total: 1,
      next_cursor: null,
      applied_filters: {},
      suggestions: [],
      facets: {},
      sort: "relevance",
    });
    const searchRes = await searchProducts({
      query: "linen blazer",
      sort: "relevance",
      currency: "USD",
    });
    expect(searchRes.items).toHaveLength(1);
    const flattened = flattenSearchPages([
      {
        items: [
          {
            product_id: "prod-1",
            merchant_product_id: "offer-a",
            title: "Navy Linen Blazer",
            brand: { id: "brand-1", name: "Studio" },
            price: { amount: 14900, currency: "USD" },
            availability: "IN_STOCK",
            matched_attributes: [],
            primary_image_url: "https://cdn.example.com/a.jpg",
          },
          {
            product_id: "prod-1",
            merchant_product_id: "offer-b",
            title: "Navy Linen Blazer",
            brand: { id: "brand-1", name: "Studio" },
            price: { amount: 15500, currency: "USD" },
            availability: "LOW_STOCK",
            matched_attributes: [],
            primary_image_url: "https://cdn.example.com/b.jpg",
          },
          {
            product_id: "prod-1",
            merchant_product_id: "offer-a",
            title: "Navy Linen Blazer",
            brand: { id: "brand-1", name: "Studio" },
            price: { amount: 14900, currency: "USD" },
            availability: "IN_STOCK",
            matched_attributes: [],
            primary_image_url: "https://cdn.example.com/a.jpg",
          },
        ],
      },
    ]);
    expect(flattened).toHaveLength(2);

    // 3. PDP & availability
    mockedApi.mockResolvedValueOnce({
      product_id: "prod-1",
      offer_id: "offer-a",
      title: "Navy Linen Blazer",
      availability: "in_stock",
      vto_eligible: true,
    });
    const detail = await fetchProductDetail("prod-1", "offer-a");
    expect(detail.offer_id).toBe("offer-a");
    expect(availabilityMessage("in_stock")).toBe("In stock");
    expect(canPurchase("in_stock")).toBe(true);
    expect(canPurchase("out_of_stock")).toBe(false);

    // 4. VTO submission, polling, cancellation, and error mapping
    mockedApi.mockResolvedValueOnce({
      job_id: "job-1",
      status: "queued",
    });
    const submitted = await submitTryOnJob({
      garmentId: "prod-1",
      idempotencyKey: "idem-09-9",
    });
    expect(submitted.job_id).toBe("job-1");

    mockedApi.mockResolvedValueOnce({
      job_id: "job-1",
      status: "succeeded",
      result_image_url: "https://cdn.example.com/result.png",
    });
    const polled = await getTryOnJob("job-1");
    expect(polled.status).toBe("succeeded");

    mockedApi.mockResolvedValueOnce({
      job_id: "job-1",
      status: "cancelled",
    });
    const cancelled = await cancelTryOnJob("job-1");
    expect(cancelled.status).toBe("cancelled");
    expect(mapTryOnErrorCode("VTO_CONSENT_REQUIRED")).toContain("Virtual Try-On consent");

    // 5. Saved look persistence
    mockedApi.mockResolvedValueOnce({
      id: "look-1",
      title: "Weekend Blazer",
      item_count: 1,
      created_at: "2026-11-28T00:00:00Z",
      updated_at: "2026-11-28T00:00:00Z",
    });
    const savedLook = await createSavedLook({
      title: "Weekend Blazer",
      item_ids: ["item-1"],
    });
    expect(savedLook.id).toBe("look-1");

    mockedApi.mockResolvedValueOnce(undefined);
    await deleteSavedLook("look-1");
    expect(mockedApi).toHaveBeenCalledWith(
      "/wardrobe/looks/look-1",
      expect.objectContaining({ method: "DELETE" }),
    );

    // 6. Merchant redirect
    mockedApi.mockResolvedValueOnce({
      redirect_url: "https://merchant.example.com/products/navy-linen-blazer",
      offer_id: "offer-a",
    });
    const redirect = await requestMerchantRedirect("offer-a");
    expect(redirect.redirect_url).toMatch(/^https:\/\//);
  });

  it("redacts tokens, signed URLs, base64 images, and local file URIs from crash reports", () => {
    const payload = captureSafeError(
      new Error(
        "Upload failed with Bearer eyJhbGciOiJIUzI1NiJ9.abc.def to https://bucket.s3.amazonaws.com/photo.jpg?X-Amz-Signature=deadbeef from file:///data/user/0/photo.jpg and data:image/png;base64,iVBORw0KGgo=",
      ),
      { feature: "tryon", screen: "PhotoPreview", requestId: "req-99" },
    );

    expect(payload.message).not.toContain("eyJhbGciOiJIUzI1NiJ9");
    expect(payload.message).not.toContain("deadbeef");
    expect(payload.message).not.toContain("file:///data/user/0");
    expect(payload.message).not.toContain("iVBORw0KGgo=");
    expect(payload.requestId).toBe("req-99");
  });
});
