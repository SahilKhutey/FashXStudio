import type {
  ColorPreference,
  StylePreference,
} from "../profile/types/profile.types";

export const ONBOARDING_STEPS = [
  "WELCOME",
  "PRODUCT_INTRO",
  "PRIVACY",
  "CONSENT",
  "BASIC_PROFILE",
  "HEIGHT",
  "MEASUREMENTS",
  "SIZE_SYSTEM",
  "FIT_PREFERENCES",
  "STYLE_PREFERENCES",
  "COLOR_PREFERENCES",
  "SAVE_PROFILE",
  "COMPLETE",
] as const;

export type OnboardingStep = (typeof ONBOARDING_STEPS)[number];

export type OnboardingStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "BASIC_PROFILE_COMPLETE"
  | "OPTIONAL_DETAILS_PENDING"
  | "COMPLETED"
  | "SKIPPED"
  | "NEEDS_RECONSENT";

export type MeasurementKey =
  | "CHEST"
  | "WAIST"
  | "HIP"
  | "SHOULDER"
  | "INSEAM"
  | "SLEEVE_LENGTH";

export type PreferredSizeSystem = "IN" | "UK" | "US" | "EU" | "INTL";

export type FitPreferenceOption =
  | "SLIM"
  | "REGULAR"
  | "RELAXED"
  | "OVERSIZED"
  | "NO_PREFERENCE";

export type OnboardingDraft = {
  displayName?: string;
  countryCode?: string;
  preferredUnit?: "CM" | "IN";
  heightCm?: number | null;
  preferredSizeSystem?: PreferredSizeSystem | null;
  measurements: Partial<Record<MeasurementKey, number>>;
  fitPreference?: FitPreferenceOption;
  stylePreferences: StylePreference[];
  colorPreferences: ColorPreference[];
  skippedSteps: OnboardingStep[];
};
