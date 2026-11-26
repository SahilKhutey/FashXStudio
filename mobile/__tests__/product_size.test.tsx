import React from "react";

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

interface TestNode {
  props: Record<string, unknown>;
  children: (TestNode | string)[];
  findAll: (predicate: (node: TestNode) => boolean) => TestNode[];
}

interface RendererInstance {
  root: TestNode;
  update: (element: React.ReactElement) => void;
}

const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => RendererInstance;
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

function textOf(node: TestNode | string): string {
  if (typeof node === "string") return node;
  return (node.children ?? []).map(textOf).join("");
}

async function renderTree(element: React.ReactElement) {
  let renderer!: RendererInstance;
  await TestRenderer.act(async () => {
    renderer = TestRenderer.create(element);
  });

  const getByText = (matcher: string | RegExp): TestNode => {
    const matches = renderer.root.findAll((node) => {
      if (typeof node.props.children === "string" || Array.isArray(node.props.children)) {
        const direct = textOf(node);
        return typeof matcher === "string" ? direct === matcher : matcher.test(direct);
      }
      return false;
    });
    const textMatches = matches.filter((n) => n.children.every((c) => typeof c === "string"));
    const hit = textMatches[0] ?? matches[0];
    if (!hit) throw new Error(`Unable to find node with text: ${String(matcher)}`);
    return hit;
  };

  const getByLabelText = (label: string): TestNode => {
    const matches = renderer.root.findAll((node) => node.props.accessibilityLabel === label);
    const hit = matches[0];
    if (!hit) throw new Error(`Unable to find node with accessibilityLabel: ${label}`);
    return hit;
  };

  const press = async (node: TestNode) => {
    await TestRenderer.act(async () => {
      const handler = node.props.onPress as (() => void) | undefined;
      if (handler) {
        handler();
      } else {
        // Walk up rendered children if Text was found inside TouchableOpacity
        const pressables = renderer.root.findAll(
          (n) =>
            typeof n.props.onPress === "function" &&
            n.findAll((c) => c === node).length > 0,
        );
        const owner = pressables[pressables.length - 1];
        if (!owner) throw new Error("Node is not pressable");
        (owner.props.onPress as () => void)();
      }
    });
  };

  return { getByText, getByLabelText, press };
}

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
      const { getByText } = await renderTree(
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
      const { getByText, press } = await renderTree(
        <ProductSizeChart chart={sampleChart} onUnitChange={onUnitChange} />,
      );

      expect(getByText("101.6")).toBeTruthy();
      expect(getByText(/Showing merchant's native INTL_ALPHA sizes/)).toBeTruthy();
      expect(getByText(/does not establish verified physical fit/)).toBeTruthy();

      await press(getByText("IN"));
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
      const { getByLabelText, press } = await renderTree(
        <AvailableSizes variants={variants} selectedSize="M" onSelectSize={onSelectSize} />,
      );

      await press(getByLabelText("Size M, IN STOCK"));
      expect(onSelectSize).toHaveBeenCalledWith("M");

      const soldOutPill = getByLabelText("Size L, SOLD OUT");
      expect((soldOutPill.props.accessibilityState as { disabled: boolean }).disabled).toBe(true);
    });
  });
});
