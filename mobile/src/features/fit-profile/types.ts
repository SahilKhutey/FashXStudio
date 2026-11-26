/**
 * Phase 08.2 - Shopper Fit Profile TypeScript Contracts
 */

export type MeasurementUnit = "CM" | "MM" | "IN" | "KG";

export type MeasurementSource = "MANUAL" | "IMPORTED";

export type MeasurementMethod =
  | "SELF_MEASURED"
  | "ASSISTED_MEASUREMENT"
  | "OTHER";

export type MeasurementStatus =
  | "NOT_PROVIDED"
  | "PROVIDED"
  | "NEEDS_REVIEW"
  | "EXPIRED"
  | "WITHDRAWN";

export type MeasurementValidationStatus =
  | "ACCEPTED"
  | "WARNING"
  | "NEEDS_CONFIRMATION"
  | "REJECTED";

export type FitPreference =
  | "SLIM"
  | "REGULAR"
  | "RELAXED"
  | "OVERSIZED"
  | "NO_PREFERENCE";

export type ConsentPurpose =
  | "fit_profile_storage"
  | "fit_recommendation_processing"
  | "third_party_fit_processing"
  | "model_training";

export interface MeasurementDefinition {
  code: string;
  display_name: string;
  explanation: string;
  tape_positioning: string;
  how_to_hold: string;
  example_input: string;
  measurement_type: string;
  supported_categories: string[];
  default_unit: MeasurementUnit;
  is_optional_contextual: boolean;
}

export interface ShopperMeasurement {
  id: string;
  field: string;
  measurement_subject: "BODY";
  value: string | number;
  unit: MeasurementUnit;
  normalized_value: string | number;
  normalized_unit: MeasurementUnit;
  source: MeasurementSource;
  measurement_method: MeasurementMethod;
  status: MeasurementStatus;
  validation_status: MeasurementValidationStatus;
  validation_message?: string | null;
  policy_version: string;
  schema_version: string;
  measured_at: string;
  created_at: string;
  updated_at: string;
  verified_at?: string | null;
  expires_at?: string | null;
  needs_confirmation: boolean;
  version: number;
}

export interface CategoryFitPreference {
  category: string;
  fit_preference: FitPreference;
  updated_at?: string | null;
}

export interface CategoryReadiness {
  category: string;
  status: "READY" | "MISSING_REQUIRED_MEASUREMENTS" | "UNSUPPORTED_CATEGORY";
  policy_version?: string | null;
  required_fields: string[];
  optional_fields: string[];
  missing_fields: string[];
  message: string;
}

export interface ShopperFitProfile {
  status: "PROFILE_READY" | "PROFILE_INCOMPLETE";
  profile_id: string;
  schema_version: string;
  preferred_unit: MeasurementUnit;
  default_fit_preference: FitPreference;
  preference_updated_at?: string | null;
  measurements: ShopperMeasurement[];
  category_preferences: CategoryFitPreference[];
  category_readiness: Record<string, CategoryReadiness>;
  consents: Record<string, boolean>;
  version: number;
}

export interface MeasurementHistoryItem {
  id: string;
  measurement_id?: string | null;
  field: string;
  previous_value?: string | number | null;
  previous_unit?: MeasurementUnit | null;
  new_value?: string | number | null;
  new_unit?: MeasurementUnit | null;
  normalized_value?: string | number | null;
  change_source: string;
  changed_at: string;
}

export interface MeasurementEntryInput {
  field: string;
  value: string | number;
  unit: MeasurementUnit;
  measured_at?: string;
  measurement_method?: MeasurementMethod;
  confirm_unusual?: boolean;
}
