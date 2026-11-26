import { create } from "zustand";

import type {
  FitFeedbackResponse,
  FitRecommendationResult,
} from "../types/fit";

interface FitRecommendationState {
  recommendation: FitRecommendationResult | null;
  feedback: FitFeedbackResponse | null;
  loading: boolean;
  submittingFeedback: boolean;
  feedbackSubmitted: boolean;
  error: string | null;
  setRecommendation: (rec: FitRecommendationResult | null) => void;
  setFeedback: (fb: FitFeedbackResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setSubmittingFeedback: (submitting: boolean) => void;
  setError: (error: string | null) => void;
  resetFitState: () => void;
}

export const useFitStore = create<FitRecommendationState>((set) => ({
  recommendation: null,
  feedback: null,
  loading: false,
  submittingFeedback: false,
  feedbackSubmitted: false,
  error: null,

  setRecommendation: (recommendation) =>
    set({
      recommendation,
      feedback: null,
      feedbackSubmitted: false,
      error: null,
    }),
  setFeedback: (feedback) =>
    set({
      feedback,
      feedbackSubmitted: feedback !== null,
      submittingFeedback: false,
    }),
  setLoading: (loading) => set({ loading }),
  setSubmittingFeedback: (submittingFeedback) => set({ submittingFeedback }),
  setError: (error) => set({ error, loading: false, submittingFeedback: false }),
  resetFitState: () =>
    set({
      recommendation: null,
      feedback: null,
      loading: false,
      submittingFeedback: false,
      feedbackSubmitted: false,
      error: null,
    }),
}));
