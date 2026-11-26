/**
 * Phase 08.2 - Shopper Fit Profile API Client
 */

import { api } from "../../../api/client";
import type {
  CategoryFitPreference,
  CategoryReadiness,
  ConsentPurpose,
  FitPreference,
  MeasurementDefinition,
  MeasurementEntryInput,
  MeasurementHistoryItem,
  MeasurementMethod,
  MeasurementUnit,
  ShopperFitProfile,
  ShopperMeasurement,
} from "../types";

export const fitProfileApi = {
  getProfile: async (): Promise<ShopperFitProfile> => {
    return api<ShopperFitProfile>("/profile/fit");
  },

  getDefinitions: async (): Promise<MeasurementDefinition[]> => {
    return api<MeasurementDefinition[]>("/profile/fit/definitions");
  },

  getCategoryPolicy: async (category: string): Promise<CategoryReadiness> => {
    return api<CategoryReadiness>(
      `/profile/fit/policies/${encodeURIComponent(category)}`,
    );
  },

  addMeasurements: async (
    measurements: MeasurementEntryInput[],
  ): Promise<ShopperFitProfile> => {
    return api<ShopperFitProfile>("/profile/fit/measurements", {
      method: "POST",
      body: JSON.stringify({ measurements }),
    });
  },

  updateMeasurement: async (
    field: string,
    payload: {
      value: string | number;
      unit: MeasurementUnit;
      expected_version: number;
      measured_at?: string;
      measurement_method?: MeasurementMethod;
      confirm_unusual?: boolean;
    },
  ): Promise<ShopperMeasurement> => {
    return api<ShopperMeasurement>(
      `/profile/fit/measurements/${encodeURIComponent(field)}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
    );
  },

  confirmMeasurement: async (field: string): Promise<ShopperMeasurement> => {
    return api<ShopperMeasurement>(
      `/profile/fit/measurements/${encodeURIComponent(field)}/confirm`,
      { method: "POST" },
    );
  },

  deleteMeasurement: async (field: string): Promise<void> => {
    return api<void>(
      `/profile/fit/measurements/${encodeURIComponent(field)}`,
      { method: "DELETE" },
    );
  },

  getHistory: async (field?: string): Promise<MeasurementHistoryItem[]> => {
    const query = field ? `?field=${encodeURIComponent(field)}` : "";
    return api<MeasurementHistoryItem[]>(
      `/profile/fit/measurements/history${query}`,
    );
  },

  updateDefaultPreference: async (
    defaultFitPreference: FitPreference,
    preferredUnit?: MeasurementUnit,
  ): Promise<ShopperFitProfile> => {
    return api<ShopperFitProfile>("/profile/fit/preferences", {
      method: "PUT",
      body: JSON.stringify({
        default_fit_preference: defaultFitPreference,
        preferred_unit: preferredUnit,
      }),
    });
  },

  updateCategoryPreference: async (
    category: string,
    fitPreference: FitPreference,
  ): Promise<CategoryFitPreference> => {
    return api<CategoryFitPreference>(
      `/profile/fit/preferences/${encodeURIComponent(category)}`,
      {
        method: "PUT",
        body: JSON.stringify({ fit_preference: fitPreference }),
      },
    );
  },

  clearCategoryPreference: async (category: string): Promise<void> => {
    return api<void>(
      `/profile/fit/preferences/${encodeURIComponent(category)}`,
      { method: "DELETE" },
    );
  },

  updateConsent: async (
    purpose: ConsentPurpose,
    granted: boolean,
    is18OrOlder?: boolean,
  ): Promise<Record<string, boolean>> => {
    return api<Record<string, boolean>>(
      `/profile/fit/consents/${encodeURIComponent(purpose)}`,
      {
        method: "PUT",
        body: JSON.stringify({
          granted,
          is_18_or_older: is18OrOlder,
        }),
      },
    );
  },

  deleteFitProfile: async (): Promise<void> => {
    return api<void>("/profile/fit", { method: "DELETE" });
  },
};
