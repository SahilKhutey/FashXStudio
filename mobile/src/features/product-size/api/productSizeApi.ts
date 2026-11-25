/**
 * Phase 08.1 - Product Size Data API Client
 */

import {
  MeasurementUnit,
  ProductSizeChartResponse,
  ProductVariantAvailability,
  SizeChartUnavailableResponse,
  SizeSystemRef,
} from "../types/sizeChart";

const BASE_URL = "/api/v1";

export async function fetchProductSizeChart(
  productId: string,
  options?: {
    unit?: MeasurementUnit;
    system?: string;
  }
): Promise<ProductSizeChartResponse | SizeChartUnavailableResponse> {
  const params = new URLSearchParams();
  if (options?.unit) params.append("unit", options.unit);
  if (options?.system) params.append("system", options.system);

  const queryStr = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${BASE_URL}/products/${productId}/size-chart${queryStr}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`Product ${productId} not found.`);
    }
    throw new Error(`Failed to fetch size chart: HTTP ${response.status}`);
  }

  return response.json();
}

export async function fetchProductVariants(
  productId: string
): Promise<ProductVariantAvailability> {
  const response = await fetch(`${BASE_URL}/products/${productId}/variants`);
  if (!response.ok) {
    throw new Error(`Failed to fetch product variants: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchSizeSystems(): Promise<SizeSystemRef[]> {
  const response = await fetch(`${BASE_URL}/size-systems`);
  if (!response.ok) {
    throw new Error(`Failed to fetch size systems: HTTP ${response.status}`);
  }
  return response.json();
}
