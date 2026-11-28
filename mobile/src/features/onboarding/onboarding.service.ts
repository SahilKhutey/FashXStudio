import { api } from "../../api/client";
import { fitProfileApi } from "../fit-profile/api/fitProfileApi";
import type { FitPreference, MeasurementUnit } from "../fit-profile/types";
import { profileApi } from "../profile/services/profileApi";
import { useOnboardingStore } from "./onboarding.store";
import type { OnboardingDraft, OnboardingStatus } from "./onboarding.types";

export type OnboardingServerProgress = {
  status: OnboardingStatus;
  last_completed_step: string | null;
  skipped_steps: string[];
  revision: number;
};

export function mapDraftToProfileUpdate(draft: OnboardingDraft) {
  return {
    display_name: draft.displayName?.trim() || undefined,
    country_code: draft.countryCode || undefined,
    preferred_unit: draft.preferredUnit ?? "CM",
    height_cm: draft.heightCm ?? undefined,
    preferred_size_system: draft.preferredSizeSystem ?? undefined,
    style_preferences: draft.stylePreferences,
    color_preferences: draft.colorPreferences,
  };
}

export const onboardingService = {
  async getProgress(): Promise<OnboardingServerProgress> {
    return api<OnboardingServerProgress>("/onboarding/progress");
  },

  async saveProfileDraft(draft: OnboardingDraft) {
    const profile = await profileApi.updateProfile(mapDraftToProfileUpdate(draft));

    const measurementEntries = Object.entries(draft.measurements)
      .filter(([, value]) => typeof value === "number" && Number.isFinite(value) && value > 0)
      .map(([field, value]) => ({
        field,
        value: Number(value),
        unit: "CM" as MeasurementUnit,
        measurement_method: "SELF_MEASURED" as const,
      }));

    if (measurementEntries.length > 0) {
      await fitProfileApi.addMeasurements(measurementEntries);
    }

    if (draft.fitPreference && draft.fitPreference !== "NO_PREFERENCE") {
      await fitProfileApi.updateDefaultPreference(
        draft.fitPreference as FitPreference,
      );
    }

    return profile;
  },
};

export async function completeOnboarding() {
  const state = useOnboardingStore.getState();
  const saved = await onboardingService.saveProfileDraft(state.draft);
  useOnboardingStore.getState().reset();
  return saved;
}
