/** Shared client-side primitives for every FashXStudio feature screen. */

export type FeatureUiState<T> =
  | { status: "uninitialized" }
  | { status: "initializing" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "empty"; message: string; actionLabel?: string }
  | { status: "error"; message: string; retryable: boolean }
  | { status: "disabled"; message: string };

export type FeatureDomain =
  | "platform"
  | "user"
  | "discovery"
  | "intelligence"
  | "outfit"
  | "content"
  | "shopping"
  | "regional"
  | "engagement";

export type FeatureStatus = "planned" | "development" | "beta" | "enabled" | "disabled";

export interface FeatureSummary {
  id: `FX-F${string}`;
  name: string;
  version: string;
  domain: FeatureDomain;
  status: FeatureStatus;
  description: string;
  depends_on: string[];
  required_core_capabilities: string[];
}

export type FeatureRuntimeState =
  | "registered"
  | "initializing"
  | "ready"
  | "loading"
  | "empty"
  | "failed"
  | "disabled";

export interface FeatureRuntimeSnapshot {
  feature_id: string;
  state: FeatureRuntimeState;
  enabled_by_configuration: boolean;
  available: boolean;
  unavailable_reasons: string[];
}

export interface FeatureAvailability {
  feature: FeatureSummary;
  available: boolean;
  unavailable_reasons: string[];
}
