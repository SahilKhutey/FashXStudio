import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { AIRecommendationContract } from "../types";

interface AIRecommendationCardProps {
  recommendation: AIRecommendationContract;
  onPressExplore?: (recommendationId: string) => void;
  onPressAction?: (actionId: string, targetId?: string | null) => void;
  testID?: string;
}

export const AIRecommendationCard: React.FC<AIRecommendationCardProps> = ({
  recommendation,
  onPressExplore,
  onPressAction,
  testID,
}) => {
  const { title, explanation, confidence, actions } = recommendation;

  return (
    <View testID={testID || `ai-recommendation-card-${recommendation.id}`} style={styles.card}>
      <View style={styles.imagePlaceholder}>
        <Text style={styles.imageTag}>RECOMMENDED DIRECTION</Text>
        {confidence && (
          <View style={styles.confidenceBadge}>
            <Text style={styles.confidenceText}>{confidence.toUpperCase()} MATCH</Text>
          </View>
        )}
      </View>

      <View style={styles.content}>
        <Text style={styles.title}>{title}</Text>

        <View style={styles.reasonBox}>
          <Text style={styles.reasonHeader}>WHY THIS WAS SUGGESTED</Text>
          <Text style={styles.reasonText} numberOfLines={2}>
            {explanation.primary_reason}
          </Text>
        </View>

        <View style={styles.actionsRow}>
          {onPressExplore && (
            <TouchableOpacity
              testID={`explore-rec-btn-${recommendation.id}`}
              style={styles.exploreButton}
              onPress={() => onPressExplore(recommendation.id)}
            >
              <Text style={styles.exploreButtonText}>Understand Reason →</Text>
            </TouchableOpacity>
          )}

          {actions &&
            actions.map((act) => (
              <TouchableOpacity
                key={act.action_id}
                testID={`rec-action-${act.action_id}`}
                style={styles.secondaryAction}
                onPress={() => onPressAction?.(act.action_id, act.target_id)}
              >
                <Text style={styles.secondaryActionText}>{act.label}</Text>
              </TouchableOpacity>
            ))}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    overflow: "hidden",
    marginBottom: 16,
  },
  imagePlaceholder: {
    height: 140,
    backgroundColor: "#2C2C2E",
    justifyContent: "space-between",
    padding: 12,
  },
  imageTag: {
    color: "#AEAEB2",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  confidenceBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#34C759",
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 4,
  },
  confidenceText: {
    color: "#FFFFFF",
    fontSize: 9,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  content: {
    padding: 14,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 8,
  },
  reasonBox: {
    backgroundColor: "#F9F9FB",
    borderRadius: 6,
    padding: 8,
    marginBottom: 12,
  },
  reasonHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  reasonText: {
    fontSize: 12,
    color: "#48484A",
    lineHeight: 16,
  },
  actionsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  exploreButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: "#F2F2F7",
  },
  exploreButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#007AFF",
  },
  secondaryAction: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: "#1C1C1E",
  },
  secondaryActionText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#FFFFFF",
  },
});
