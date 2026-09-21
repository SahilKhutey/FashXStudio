import { apiClient } from "../../api/client";

import type { FeatureAvailability, FeatureRuntimeSnapshot, FeatureSummary } from "./types";

/** Read-only feature metadata; feature UI must not assume a planned feature is usable. */
export function getFeatures(): Promise<FeatureSummary[]> {
  return apiClient<FeatureSummary[]>("/api/v1/features");
}

export function getFeatureAvailability(featureId: string): Promise<FeatureAvailability> {
  return apiClient<FeatureAvailability>(`/api/v1/features/${featureId}`);
}

export function initializeFeatureRuntime(): Promise<FeatureRuntimeSnapshot[]> {
  return apiClient<FeatureRuntimeSnapshot[]>("/api/v1/features/runtime");
}
