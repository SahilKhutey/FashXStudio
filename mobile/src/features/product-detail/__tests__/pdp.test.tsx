import React from "react";
import { formatMinorPrice, getDiscountPercentage } from "../utils/formatPrice";
import { availabilityMessage, canPurchase } from "../utils/availability";
import { ProductGallery } from "../components/ProductGallery";
import { fetchProductDetail, requestMerchantRedirect } from "../api";
import { api } from "../../../api/client";

jest.mock("../../../api/client", () => ({
  api: jest.fn(),
  apiClient: jest.fn(),
}));

// eslint-disable-next-line @typescript-eslint/no-require-imports
const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => {
    toJSON: () => unknown;
  };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 09.5 product price formatting (PDP-MOB)", () => {
  it("formats INR minor units and computes only valid discounts", () => {
    expect(formatMinorPrice(149900, "INR")).toContain("1,499");
    expect(formatMinorPrice(-10, "INR")).toBe("Price unavailable");
    expect(getDiscountPercentage(149900, null)).toBeNull();
    expect(getDiscountPercentage(15000, 20000)).toBe(25);
    expect(getDiscountPercentage(22000, 20000)).toBeNull();
  });
});

describe("Phase 09.5 product availability helper (PDP-MOB)", () => {
  it("never treats unknown or delisted stock as purchasable", () => {
    expect(canPurchase("unknown")).toBe(false);
    expect(canPurchase("delisted")).toBe(false);
    expect(canPurchase("taken_down")).toBe(false);
    expect(canPurchase("in_stock")).toBe(true);
    expect(canPurchase("low_stock")).toBe(true);
    expect(availabilityMessage("stale")).toMatch(/refreshed/i);
  });
});

describe("Phase 09.5 ProductGallery & API client calls", () => {
  it("renders fallback when no authorized images exist and counter when images exist", async () => {
    let emptyTree!: { toJSON: () => unknown };
    let galleryTree!: { toJSON: () => unknown };

    await TestRenderer.act(async () => {
      emptyTree = TestRenderer.create(<ProductGallery images={[]} />);
      galleryTree = TestRenderer.create(
        <ProductGallery
          images={[
            {
              id: "img-1",
              url: "https://cdn.fashxstudio.com/1.jpg",
              alt_text: "Front view",
              position: 0,
              is_primary: true,
            },
          ]}
        />,
      );
    });

    expect(JSON.stringify(emptyTree.toJSON())).toContain("Product image unavailable");
    expect(JSON.stringify(galleryTree.toJSON())).toContain('"1"," / ","1"');
  });

  it("calls exact offer-scoped detail and redirect endpoints", async () => {
    (api as jest.Mock).mockResolvedValue({ ok: true });
    await fetchProductDetail("prd-1", "off-1");
    expect(api).toHaveBeenCalledWith(
      "/catalog/products/prd-1/detail?offer_id=off-1",
      { method: "GET" },
    );

    await requestMerchantRedirect("off-1");
    expect(api).toHaveBeenCalledWith(
      "/catalog/offers/off-1/redirect",
      { method: "POST", body: JSON.stringify({}) },
    );
  });
});
