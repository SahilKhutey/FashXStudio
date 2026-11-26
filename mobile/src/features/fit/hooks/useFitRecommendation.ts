import { useCallback } from "react";

import { evaluateFitRecommendation, submitFitFeedback } from "../api/fitApi";
import { useFitStore } from "../store/fitStore";
import type {
  FitFeedbackCreateRequest,
  FitRecommendationRequest,
} from "../types/fit";

export function useFitRecommendation() {
  const recommendation = useFitStore((s) => s.recommendation);
  const feedback = useFitStore((s) => s.feedback);
  const loading = useFitStore((s) => s.loading);
  const submittingFeedback = useFitStore((s) => s.submittingFeedback);
  const feedbackSubmitted = useFitStore((s) => s.feedbackSubmitted);
  const error = useFitStore((s) => s.error);
  const setRecommendation = useFitStore((s) => s.setRecommendation);
  const setFeedback = useFitStore((s) => s.setFeedback);
  const setLoading = useFitStore((s) => s.setLoading);
  const setSubmittingFeedback = useFitStore((s) => s.setSubmittingFeedback);
  const setError = useFitStore((s) => s.setError);
  const resetFitState = useFitStore((s) => s.resetFitState);

  const fetchRecommendation = useCallback(
    async (req: FitRecommendationRequest) => {
      setLoading(true);
      setError(null);
      try {
        const res = await evaluateFitRecommendation(req);
        setRecommendation(res);
        setLoading(false);
        return res;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Unable to load fit guidance.";
        setError(msg);
        return null;
      }
    },
    [setError, setLoading, setRecommendation],
  );

  const sendFeedback = useCallback(
    async (recommendationId: string, payload: FitFeedbackCreateRequest) => {
      setSubmittingFeedback(true);
      try {
        const res = await submitFitFeedback(recommendationId, payload);
        setFeedback(res);
        return res;
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Unable to submit feedback.";
        setError(msg);
        return null;
      }
    },
    [setError, setFeedback, setSubmittingFeedback],
  );

  return {
    recommendation,
    feedback,
    loading,
    submittingFeedback,
    feedbackSubmitted,
    error,
    fetchRecommendation,
    sendFeedback,
    resetFitState,
  };
}
