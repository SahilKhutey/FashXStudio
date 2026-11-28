import React from "react";
import { api } from "../src/api/client";
import { flattenSearchPages } from "../src/features/catalog/flatten-pages";
import { ProductSearchResponseSchema } from "../src/features/catalog/catalog.schema";
import {
  isSafeMerchantUrl,
  priceToMinorUnits,
} from "../src/features/catalog/utils/product-links";
import {
  clearSearchFilters,
  defaultSearchFilters,
  updateSearchSort,
  validatePriceRange,
} from "../src/features/search/search.filters";
import { buildSearchQueryParams, searchProducts } from "../src/features/search/search.api";
import { PriceDisplay } from "../src/features/catalog/components/PriceDisplay";
import { EmptyProducts } from "../src/features/catalog/components/EmptyProducts";
import { ProductError } from "../src/features/catalog/components/ProductError";

jest.mock("../src/api/client", () => ({
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

const sampleItem = {
  product_id: "prd-1",
  merchant_product_id: "off-1",
  title: "Men's Cotton Casual Shirt",
  brand: { id: "brand-1", name: "Example Brand" },
  price: { amount: "1299.00", currency: "INR" },
  availability: "IN_STOCK",
  matched_attributes: ["cotton"],
  primary_image_url: "https://cdn.fashxstudio.com/shirts/1.jpg",
};

describe("Phase 09.4 search filters, params, and schema validation", () => {
  it("builds search query params and resets cursor on sort/filter clear", () => {
    const sorted = updateSearchSort(
      { ...defaultSearchFilters, query: "kurta", cursor: "cur-1" },
      "price_low",
    );
    expect(sorted.cursor).toBeUndefined();
    expect(sorted.sort).toBe("price_low");

    const qs = buildSearchQueryParams({ ...sorted, inStock: true, size: "M" }, 20);
    expect(qs).toContain("q=kurta");
    expect(qs).toContain("sort=price_low");
    expect(qs).toContain("in_stock=true");
    expect(qs).toContain("size=M");

    const cleared = clearSearchFilters({ ...sorted, minPrice: 500, size: "M" });
    expect(cleared.minPrice).toBeUndefined();
    expect(cleared.size).toBeUndefined();
    expect(cleared.query).toBe("kurta");
  });

  it("validates price range bounds", () => {
    expect(validatePriceRange(500, 1500)).toBe(true);
    expect(validatePriceRange(1500, 500)).toBe(false);
    expect(validatePriceRange(-10, 500)).toBe(false);
  });

  it("validates ProductSearchResponse via Zod and rejects malformed payloads", async () => {
    (api as jest.Mock).mockResolvedValue({
      search_id: "11111111-1111-4111-8111-111111111111",
      query: "shirt",
      items: [sampleItem],
      total: 1,
      next_cursor: "cur-2",
      applied_filters: {},
      suggestions: [],
      facets: {},
      sort: "relevance",
    });

    const res = await searchProducts({ ...defaultSearchFilters, query: "shirt" });
    expect(res.items).toHaveLength(1);
    expect(res.next_cursor).toBe("cur-2");

    expect(() =>
      ProductSearchResponseSchema.parse({ search_id: "s1", items: [{ title: "" }] }),
    ).toThrow();
  });
});

describe("Phase 09.4 pagination deduplication & URL/price helpers", () => {
  it("deduplicates identical product+offer pairs while preserving separate merchant offers", () => {
    const otherOffer = { ...sampleItem, merchant_product_id: "off-2" };
    const flattened = flattenSearchPages([
      { items: [sampleItem] },
      { items: [sampleItem, otherOffer] },
    ]);
    expect(flattened).toHaveLength(2);
    expect(flattened.map((i) => i.merchant_product_id)).toEqual(["off-1", "off-2"]);
  });

  it("enforces HTTPS-only merchant URLs and converts prices to minor units", () => {
    expect(isSafeMerchantUrl("https://merchant.example.com/p/1")).toBe(true);
    expect(isSafeMerchantUrl("http://merchant.example.com/p/1")).toBe(false);
    expect(isSafeMerchantUrl("javascript:alert(1)")).toBe(false);
    expect(priceToMinorUnits("1299.50")).toBe(129950);
    expect(priceToMinorUnits("invalid")).toBe(0);
  });
});

describe("Phase 09.4 discovery UI components (PRICE, EMPTY, ERR)", () => {
  it("renders PriceDisplay, EmptyProducts, and ProductError cleanly", async () => {
    let priceTree!: { toJSON: () => unknown };
    let missingPriceTree!: { toJSON: () => unknown };
    let emptyTree!: { toJSON: () => unknown };
    let errorTree!: { toJSON: () => unknown };

    await TestRenderer.act(async () => {
      priceTree = TestRenderer.create(
        <PriceDisplay price={{ amount: "1299.00", currency: "INR" }} />,
      );
      missingPriceTree = TestRenderer.create(<PriceDisplay price={null} />);
      emptyTree = TestRenderer.create(<EmptyProducts onClear={jest.fn()} />);
      errorTree = TestRenderer.create(<ProductError onRetry={jest.fn()} />);
    });

    expect(JSON.stringify(priceTree.toJSON())).toContain("1,299");
    expect(JSON.stringify(missingPriceTree.toJSON())).toContain("Price unavailable");
    expect(JSON.stringify(emptyTree.toJSON())).toContain("No products found");
    expect(JSON.stringify(errorTree.toJSON())).toContain("Try again");
  });
});
