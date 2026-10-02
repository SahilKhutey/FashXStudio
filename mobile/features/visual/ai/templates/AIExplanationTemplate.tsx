import React, { useState } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIResultExplanationTemplateSpecContract, AIFeedbackReason, AIFeedbackType } from "../types";
import { AIExplanationCard } from "../components/AIExplanationCard";
import { AIFeedbackModal } from "../components/AIFeedbackModal";

interface AIExplanationTemplateProps {
  data: AIResultExplanationTemplateSpecContract;
  onSubmitFeedback?: (
    resultId: string,
    feedbackType: AIFeedbackType,
    reason?: AIFeedbackReason,
  ) => void;
  testID?: string;
}

export const AIExplanationTemplate: React.FC<AIExplanationTemplateProps> = ({
  data,
  onSubmitFeedback,
  testID = "ai-explanation-screen",
}) => {
  const { result_id, target_item, explanation, user_feedback } = data;
  const [feedbackModalVisible, setFeedbackModalVisible] = useState(false);

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTag}>RESULT EXPLANATION</Text>
          <Text style={styles.title}>Why was this item suggested?</Text>
        </View>

        {/* Target Item Summary */}
        <View style={styles.targetCard}>
          <View style={styles.targetThumb}>
            <Text style={styles.targetThumbText}>{target_item.media_type.toUpperCase()}</Text>
          </View>
          <View style={styles.targetInfo}>
            <Text style={styles.targetTitle}>{target_item.title}</Text>
            {target_item.subtitle && (
              <Text style={styles.targetSubtitle}>{target_item.subtitle}</Text>
            )}
          </View>
        </View>

        {/* Structured Explanation */}
        <AIExplanationCard explanation={explanation} />

        {/* Feedback Section */}
        <View style={styles.feedbackSection}>
          <Text style={styles.feedbackHeader}>WAS THIS EXPLANATION HELPFUL?</Text>
          {user_feedback ? (
            <View style={styles.feedbackSubmittedBox}>
              <Text style={styles.feedbackSubmittedText}>
                ✓ Feedback submitted: {user_feedback.feedback_type === "helpful" ? "Helpful" : "Needs Improvement"}
              </Text>
            </View>
          ) : (
            <TouchableOpacity
              testID="open-feedback-modal-btn"
              style={styles.giveFeedbackBtn}
              onPress={() => setFeedbackModalVisible(true)}
            >
              <Text style={styles.giveFeedbackText}>Provide Feedback on this Recommendation</Text>
            </TouchableOpacity>
          )}
        </View>
      </ScrollView>

      {onSubmitFeedback && (
        <AIFeedbackModal
          visible={feedbackModalVisible}
          resultId={result_id}
          onClose={() => setFeedbackModalVisible(false)}
          onSubmitFeedback={onSubmitFeedback}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FDFDFD",
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 16,
  },
  headerTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 1,
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  targetCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 12,
    marginBottom: 16,
  },
  targetThumb: {
    width: 48,
    height: 48,
    backgroundColor: "#F2F2F7",
    borderRadius: 4,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  targetThumbText: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
  },
  targetInfo: {
    flex: 1,
  },
  targetTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  targetSubtitle: {
    fontSize: 12,
    color: "#636366",
    marginTop: 2,
  },
  feedbackSection: {
    marginTop: 16,
    padding: 16,
    backgroundColor: "#F9F9FB",
    borderRadius: 8,
  },
  feedbackHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  feedbackSubmittedBox: {
    backgroundColor: "#E8F8EE",
    padding: 10,
    borderRadius: 6,
  },
  feedbackSubmittedText: {
    fontSize: 12,
    color: "#1B7C3E",
    fontWeight: "600",
  },
  giveFeedbackBtn: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#D1D1D6",
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: "center",
  },
  giveFeedbackText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
