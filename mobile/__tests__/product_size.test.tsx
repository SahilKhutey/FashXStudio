import React from "react";
import { fireEvent, render } from "@testing-library/react-native";

import {
  fetchProductSizeChart,
  fetchProductVariants,
  fetchSizeSystems,
} from "../src/features/product-size/api/productSizeApi";
import { AvailableSizes } from "../src/features/product-size/components/AvailableSizes";
import { ProductSizeChart } from "../src/features/product-size/components/ProductSizeChart";
import type {
  ProductSizeChartResponse,
  VariantStockItem,
} from "../src/features/product-size/types/sizeChart";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
}));

describe("Phase 08.1 Mobile: Product Size Data", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("productSizeApi", () => {
    it("fetches product size chart with unit and system query parameters via api client", async () => {
      const { api } = require("../src/api/client");
      const mockResp = { product_id: "prod-1", status: "UNAVAILABLE", message: "Unavailable" };
      (api as jest.Mock).mockResolvedValue(mockResp);

      const res = await fetchProductSizeChart("prod-1", { unit: "INCH", system: "US_NUMERIC_WOMEN" });

      expect(api).toHaveBeenCalledWith(
        "/products/prod-1/size-chart?unit=INCH&system=US_NUMERIC_WOMEN",
      );
      expect(res).toEqual(mockResp);
    });

    it("fetches product variants and size systems via api client", async () => {
      const { api } = require("../src/api/client");
      (api as jest.Mock).mockResolvedValue({ variants: [] });

      await fetchProductVariants("prod/1");
      expect(api).toHaveBeenCalledWith("/products/prod%2F1/variants");

      await fetchSizeSystems();
      expect(api).toHaveBeenCalledWith("/size-systems");
    });
  });

  describe("ProductSizeChart component", () => {
    const sampleChart: ProductSizeChartResponse = {
      chart_id: "chart-1",
      merchant_product_id: "prod-1",
      merchant_id: "merchant-1",
      version: 2,
      content_fingerprint: "sha256-hash",
      size_system: {
        code: "INTL_ALPHA",
        system_type: "REGIONAL_STANDARD",
        display_name: "International Alpha",
        mapping_status: "UNMAPPED",
      },
      measurement_basis: "GARMENT",
      display_unit: "CM",
      status: "AVAILABLE",
      is_stale: false,
      provenance: {
        source_id: "MERCHANT_PORTAL",
        source_revision: "rev-2",
        retrieved_at: "2026-11-25T10:00:00Z",
        verified_at: "2026-11-25T10:00:00Z",
      },
      rows: [
        {
          merchant_size: "M",
          mapped_size: null,
          sort_order: 0,
          measurements: [
            {
              field_code: "CHEST",
              display_name: "Chest",
              value: 101.6,
              unit: "CM",
              normalized_cm: 101.6,
            },
          ],
        },
      ],
      last_verified_at: "2026-11-25T10:00:00Z",
    };

    it("renders fail-closed unavailable card and VTO disclaimer when chart is unavailable", async () => {
      const { getByText } = await render(
        <ProductSizeChart
          chart={{
            product_id: "prod-1",
            status: "UNAVAILABLE",
            message: "No chart",
          }}
        />,
      );

      expect(getByText("Size chart not available")).toBeTruthy();
      expect(getByText(/Virtual try-on simulates appearance only/)).toBeTruthy();
    });

    it("renders chart measurements, unmapped warning, and converts CM to IN on toggle", async () => {
      const onUnitChange = jest.fn();
      const { getByText } = await render(
        <ProductSizeChart chart={sampleChart} onUnitChange={onUnitChange} />,
      );

      expect(getByText("101.6")).toBeTruthy();
      expect(getByText(/Showing merchant's native INTL_ALPHA sizes/)).toBeTruthy();
      expect(getByText(/does not establish verified physical fit/)).toBeTruthy();

      await fireEvent.press(getByText("IN"));
      expect(onUnitChange).toHaveBeenCalledWith("INCH");
      expect(getByText("40")).toBeTruthy();
    });
  });

  describe("AvailableSizes component", () => {
    const variants: VariantStockItem[] = [
      {
        variant_id: "v1",
        size_label: "M",
        status: "IN_STOCK",
        is_stale: false,
        observed_at: "2026-11-25T10:00:00Z",
      },
      {
        variant_id: "v2",
        size_label: "L",
        status: "OUT_OF_STOCK",
        is_stale: false,
        observed_at: "2026-11-25T10:00:00Z",
      },
    ];

    it("allows selecting IN_STOCK sizes and marks OUT_OF_STOCK disabled", async () => {
      const onSelectSize = jest.fn();
      const { getByLabelText } = await render(
        <AvailableSizes variants={variants} selectedSize="M" onSelectSize={onSelectSize} />,
      );

      await fireEvent.press(getByLabelText("Size M, IN STOCK"));
      expect(onSelectSize).toHaveBeenCalledWith("M");

      const soldOutPill = getByLabelText("Size L, SOLD OUT");
      expect(soldOutPill.props.accessibilityState.disabled).toBe(true);
    });
  });
});
