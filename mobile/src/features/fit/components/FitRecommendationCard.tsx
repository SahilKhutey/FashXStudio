import React from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";

import type {
  FitFeedbackCreateRequest,
  FitRecommendationResult,
} from "../types/fit";
import { FitDisclaimer } from "./FitDisclaimer";
import { FitEvidenceList } from "./FitEvidenceList";
import { FitExplanation } from "./FitExplanation";
import { FitFeedbackForm } from "./FitFeedbackForm";

export interface FitRecommendationCardProps {
  recommendation: FitRecommendationResult | null;
  loading?: boolean;
  error?: string | null;
  submittingFeedback?: boolean;
  feedbackSubmitted?: boolean;
  onRetry?: () => void;
  onSubmitFeedback?: (
    recommendationId: string,
    payload: FitFeedbackCreateRequest,
  ) => Promise<unknown> | void;
}

const STATUS_BADGE: Record<string, string> = {
  RECOMMENDED: "Product size guidance",
  POSSIBLE_ALTERNATIVES: "Multiple sizes match",
  INSUFFICIENT_INFORMATION: "More information needed",
  NO_AVAILABLE_SIZE: "No matching available size",
  UNSUPPORTED_CATEGORY: "Category guidance unavailable",
  STALE_DATA: "Size information needs update",
  CONFLICTING_DATA: "Conflicting sizing information",
};

export function FitRecommendationCard({
  recommendation,
  loading = false,
  error = null,
  submittingFeedback = false,
  feedbackSubmitted = false,
  onRetry,
  onSubmitFeedback,
}: FitRecommendationCardProps) {
  if (loading) {
    return (
      <View style={styles.card} testID="fit-recommendation-loading">
        <ActivityIndicator size="small" />
        <Text style={styles.loadingText}>Evaluating published merchant chart...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.card} testID="fit-recommendation-error">
        <Text style={styles.title}>Size guidance unavailable</Text>
        <Text style={styles.errorText}>{error}</Text>
        {onRetry && (
          <TouchableOpacity accessibilityRole="button" style={styles.retryBtn} onPress={onRetry}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        )}
        <FitDisclaimer />
      </View>
    );
  }

  if (!recommendation) {
    return null;
  }

  const badgeLabel = STATUS_BADGE[recommendation.status] || "Size guidance";
  const showCalibratedScore =
    recommendation.confidence.display_to_shopper === true &&
    recommendation.confidence.type === "CALIBRATED_PROBABILITY";

  return (
    <View style={styles.card} testID={`fit-recommendation-${recommendation.status}`}>
      <Text style={styles.kicker}>{badgeLabel}</Text>

      {recommendation.status === "RECOMMENDED" && recommendation.recommended_size && (
        <Text style={styles.sizeHighlight} testID="recommended-size-label">
          Size {recommendation.recommended_size.merchant_size_label}
        </Text>
      )}

      {recommendation.status === "POSSIBLE_ALTERNATIVES" &&
        recommendation.alternative_sizes.length > 0 && (
          <Text style={styles.sizeHighlight} testID="alternative-sizes-label">
            Options:{" "}
            {recommendation.alternative_sizes.map((s) => s.merchant_size_label).join(" or ")}
          </Text>
        )}

      {showCalibratedScore && (
        <Text style={styles.calibratedText}>
          Confidence: {String(recommendation.confidence.score)}
        </Text>
      )}

      <FitExplanation
        summary={recommendation.explanation}
        details={recommendation.explanations}
        nextActions={recommendation.next_actions}
      />

      <FitEvidenceList evidence={recommendation.evidence} />

      <FitDisclaimer text={recommendation.disclaimer} />

      {onSubmitFeedback && (
        <FitFeedbackForm
          recommendationId={recommendation.recommendation_id}
          submitting={submittingFeedback}
          submitted={feedbackSubmitted}
          onSubmit={onSubmitFeedback}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    padding: 14,
  },
  kicker: {
    fontSize: 12,
    fontWeight: "600",
    textTransform: "uppercase",
    color: "#6B7280",
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
  },
  sizeHighlight: {
    marginTop: 4,
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
  },
  calibratedText: {
    marginTop: 2,
    fontSize: 12,
    color: "#4B5563",
  },
  loadingText: {
    marginTop: 8,
    fontSize: 13,
    color: "#4B5563",
  },
  errorText: {
    marginTop: 6,
    fontSize: 13,
    color: "#B91C1C",
  },
  retryBtn: {
    marginTop: 8,
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: "#111827",
  },
  retryText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
});
