import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Modal } from "react-native";
import { AIFeedbackReason, AIFeedbackType } from "../types";

interface AIFeedbackModalProps {
  visible: boolean;
  resultId: string;
  onClose: () => void;
  onSubmitFeedback: (
    resultId: string,
    feedbackType: AIFeedbackType,
    reason?: AIFeedbackReason,
  ) => void;
  testID?: string;
}

export const AIFeedbackModal: React.FC<AIFeedbackModalProps> = ({
  visible,
  resultId,
  onClose,
  onSubmitFeedback,
  testID = "ai-feedback-modal-component",
}) => {
  const [selectedType, setSelectedType] = useState<AIFeedbackType | null>(null);
  const [selectedReason, setSelectedReason] = useState<AIFeedbackReason | null>(null);

  const handleSubmit = () => {
    if (selectedType) {
      onSubmitFeedback(resultId, selectedType, selectedReason || undefined);
      setSelectedType(null);
      setSelectedReason(null);
      onClose();
    }
  };

  const reasons: { label: string; value: AIFeedbackReason }[] = [
    { label: "Wrong Style Direction", value: "wrong_style" },
    { label: "Irrelevant Product", value: "wrong_product" },
    { label: "Too Expensive", value: "too_expensive" },
    { label: "Already Own Similar", value: "already_own" },
    { label: "Other", value: "other" },
  ];

  return (
    <Modal
      testID={testID}
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.content}>
          <Text style={styles.title}>How was this recommendation?</Text>
          <Text style={styles.subtitle}>
            Your feedback improves future suggestions without altering saved profiles.
          </Text>

          <View style={styles.typeButtonsRow}>
            <TouchableOpacity
              testID="feedback-type-helpful"
              style={[
                styles.typeButton,
                selectedType === "helpful" && styles.typeButtonSelected,
              ]}
              onPress={() => setSelectedType("helpful")}
            >
              <Text style={styles.typeButtonText}>👍 Helpful</Text>
            </TouchableOpacity>

            <TouchableOpacity
              testID="feedback-type-not-helpful"
              style={[
                styles.typeButton,
                selectedType === "not_helpful" && styles.typeButtonSelected,
              ]}
              onPress={() => setSelectedType("not_helpful")}
            >
              <Text style={styles.typeButtonText}>👎 Not Helpful</Text>
            </TouchableOpacity>
          </View>

          {selectedType === "not_helpful" && (
            <View style={styles.reasonsContainer}>
              <Text style={styles.reasonsHeader}>WHAT COULD BE BETTER?</Text>
              <View style={styles.reasonsGrid}>
                {reasons.map((r) => (
                  <TouchableOpacity
                    key={r.value}
                    testID={`feedback-reason-${r.value}`}
                    style={[
                      styles.reasonChip,
                      selectedReason === r.value && styles.reasonChipSelected,
                    ]}
                    onPress={() => setSelectedReason(r.value)}
                  >
                    <Text
                      style={[
                        styles.reasonChipText,
                        selectedReason === r.value && styles.reasonChipTextSelected,
                      ]}
                    >
                      {r.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          <View style={styles.actionRow}>
            <TouchableOpacity
              testID="feedback-cancel-btn"
              style={styles.cancelBtn}
              onPress={onClose}
            >
              <Text style={styles.cancelBtnText}>Dismiss</Text>
            </TouchableOpacity>

            <TouchableOpacity
              testID="feedback-submit-btn"
              style={[styles.submitBtn, !selectedType && styles.submitBtnDisabled]}
              disabled={!selectedType}
              onPress={handleSubmit}
            >
              <Text style={styles.submitBtnText}>Submit</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  content: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 20,
    width: "100%",
    maxWidth: 400,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    color: "#636366",
    lineHeight: 16,
    marginBottom: 16,
  },
  typeButtonsRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 16,
  },
  typeButton: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  typeButtonSelected: {
    backgroundColor: "#E5E5EA",
    borderColor: "#1C1C1E",
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  reasonsContainer: {
    marginBottom: 16,
  },
  reasonsHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  reasonsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  reasonChip: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 6,
  },
  reasonChipSelected: {
    backgroundColor: "#1C1C1E",
  },
  reasonChipText: {
    fontSize: 11,
    color: "#3A3A3C",
  },
  reasonChipTextSelected: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
  actionRow: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 12,
    marginTop: 8,
  },
  cancelBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  cancelBtnText: {
    fontSize: 13,
    color: "#8E8E93",
  },
  submitBtn: {
    backgroundColor: "#1C1C1E",
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  submitBtnDisabled: {
    backgroundColor: "#C7C7CC",
  },
  submitBtnText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
});
