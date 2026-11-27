import { apiClient } from "../../api/client";
import type {
  FeedbackType,
  RankedProductsResponse,
  RankingContextPayload,
} from "./ranking.types";

export async function fetchPersonalizedRanking(
  context: RankingContextPayload,
  rankingVersion = "personalized-v1",
): Promise<RankedProductsResponse> {
  return apiClient<RankedProductsResponse>("/api/v1/ranking/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      context,
      ranking_version: rankingVersion,
    }),
  });
}

export async function submitProductFeedback(
  productId: string,
  feedbackType: FeedbackType,
): Promise<{ product_id: string; feedback_type: FeedbackType; is_active: boolean }> {
  return apiClient(`/api/v1/products/${encodeURIComponent(productId)}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback_type: feedbackType, source: "mobile" }),
  });
}
