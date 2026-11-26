/**
 * Phase 08.1 - Product Size Data TypeScript Contracts
 */

export type MeasurementUnit = "CM" | "INCH" | "MM";

export type MeasurementBasis = "BODY" | "GARMENT";

export type SizeChartStatus = "AVAILABLE" | "UNAVAILABLE" | "STALE" | "QUARANTINED";

export type AvailabilityStatus =
  | "IN_STOCK"
  | "LOW_STOCK"
  | "OUT_OF_STOCK"
  | "PREORDER"
  | "UNKNOWN";

export type MappingStatus = "NATIVE" | "VERIFIED_MAPPING" | "UNMAPPED";

export interface SizeSystemRef {
  code: string;
  system_type: string;
  display_name: string;
  mapping_status: MappingStatus;
}

export interface SourceProvenance {
  source_id?: string | null;
  source_revision?: string | null;
  retrieved_at: string;
  verified_at?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface SizeMeasurementResponse {
  field_code: string;
  display_name: string;
  value: number;
  unit: MeasurementUnit;
  normalized_cm: number;
}

export interface SizeChartRowResponse {
  merchant_size: string;
  mapped_size?: string | null;
  sort_order: number;
  measurements: SizeMeasurementResponse[];
}

export interface ProductSizeChartResponse {
  chart_id: string;
  merchant_product_id: string;
  merchant_id: string;
  version: number;
  content_fingerprint: string;
  size_system: SizeSystemRef;
  measurement_basis: MeasurementBasis;
  display_unit: MeasurementUnit;
  status: SizeChartStatus;
  is_stale: boolean;
  provenance: SourceProvenance;
  rows: SizeChartRowResponse[];
  last_verified_at: string;
}

export interface SizeChartUnavailableResponse {
  product_id: string;
  status: "UNAVAILABLE";
  message: string;
}

export interface VariantStockItem {
  variant_id: string;
  size_label: string;
  colour_label?: string | null;
  sku?: string | null;
  status: AvailabilityStatus;
  is_stale: boolean;
  observed_at: string;
}

export interface ProductVariantAvailability {
  merchant_product_id: string;
  overall_status: AvailabilityStatus;
  variants: VariantStockItem[];
  last_checked_at: string;
}
