import { api } from "../../../api/client";
import type {
  FitFeedbackCreateRequest,
  FitFeedbackResponse,
  FitRecommendationRequest,
  FitRecommendationResult,
} from "../types/fit";

export async function evaluateFitRecommendation(
  payload: FitRecommendationRequest,
): Promise<FitRecommendationResult> {
  return api<FitRecommendationResult>("/fit/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getFitRecommendation(
  recommendationId: string,
): Promise<FitRecommendationResult> {
  return api<FitRecommendationResult>(
    `/fit/recommendations/${encodeURIComponent(recommendationId)}`,
  );
}

export async function submitFitFeedback(
  recommendationId: string,
  payload: FitFeedbackCreateRequest,
): Promise<FitFeedbackResponse> {
  return api<FitFeedbackResponse>(
    `/fit/recommendations/${encodeURIComponent(recommendationId)}/feedback`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function getFitFeedback(
  recommendationId: string,
): Promise<FitFeedbackResponse> {
  return api<FitFeedbackResponse>(
    `/fit/recommendations/${encodeURIComponent(recommendationId)}/feedback`,
  );
}
