/**
 * Phase 08.1 - Product Size Data API Client
 */

import { api } from "../../../api/client";
import {
  MeasurementUnit,
  ProductSizeChartResponse,
  ProductVariantAvailability,
  SizeChartUnavailableResponse,
  SizeSystemRef,
} from "../types/sizeChart";

export async function fetchProductSizeChart(
  productId: string,
  options?: {
    unit?: MeasurementUnit;
    system?: string;
  },
): Promise<ProductSizeChartResponse | SizeChartUnavailableResponse> {
  const params = new URLSearchParams();
  if (options?.unit) params.append("unit", options.unit);
  if (options?.system) params.append("system", options.system);

  const queryStr = params.toString() ? `?${params.toString()}` : "";
  return api<ProductSizeChartResponse | SizeChartUnavailableResponse>(
    `/products/${encodeURIComponent(productId)}/size-chart${queryStr}`,
  );
}

export async function fetchProductVariants(
  productId: string,
): Promise<ProductVariantAvailability> {
  return api<ProductVariantAvailability>(
    `/products/${encodeURIComponent(productId)}/variants`,
  );
}

export async function fetchSizeSystems(): Promise<SizeSystemRef[]> {
  return api<SizeSystemRef[]>("/size-systems");
}
