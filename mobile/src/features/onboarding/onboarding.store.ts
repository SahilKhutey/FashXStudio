import { create } from "zustand";
import type { OnboardingDraft, OnboardingStep } from "./onboarding.types";

type OnboardingState = {
  currentStep: OnboardingStep;
  draft: OnboardingDraft;
  setStep: (step: OnboardingStep) => void;
  updateDraft: (values: Partial<OnboardingDraft>) => void;
  skipStep: (step: OnboardingStep) => void;
  reset: () => void;
};

const initialDraft: OnboardingDraft = {
  measurements: {},
  stylePreferences: [],
  colorPreferences: [],
  skippedSteps: [],
};

/**
 * In-memory Zustand store for transient onboarding draft state.
 * Never persisted as a substitute for the authoritative backend profile.
 */
export const useOnboardingStore = create<OnboardingState>((set) => ({
  currentStep: "WELCOME",
  draft: initialDraft,
  setStep: (currentStep) => set({ currentStep }),
  updateDraft: (values) =>
    set((state) => ({
      draft: {
        ...state.draft,
        ...values,
      },
    })),
  skipStep: (step) =>
    set((state) => ({
      draft: {
        ...state.draft,
        skippedSteps: Array.from(new Set([...state.draft.skippedSteps, step])),
      },
    })),
  reset: () => set({ currentStep: "WELCOME", draft: initialDraft }),
}));
