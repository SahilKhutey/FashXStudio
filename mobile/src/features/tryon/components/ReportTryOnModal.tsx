import React, { useState } from "react";
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

export type FeedbackReasonCode =
  | "GARMENT_LOOKS_DIFFERENT"
  | "COLOUR_OR_PATTERN_CHANGED"
  | "GARMENT_LENGTH_OR_SHAPE"
  | "BODY_ALIGNMENT_ISSUE"
  | "FACE_OR_BODY_CHANGED"
  | "MISLEADING_FIT_IMPRESSION"
  | "LAYERING_ERROR"
  | "IMAGE_ARTIFACT"
  | "OTHER";

export interface ReportTryOnModalProps {
  visible: boolean;
  jobId: string;
  onClose: () => void;
  onSubmit: (params: {
    jobId: string;
    reasonCode: FeedbackReasonCode;
    details?: string;
    includeInQualityReview: boolean;
  }) => Promise<void>;
}

const REASON_OPTIONS: { code: FeedbackReasonCode; label: string }[] = [
  { code: "GARMENT_LOOKS_DIFFERENT", label: "Garment looks different from the product" },
  { code: "COLOUR_OR_PATTERN_CHANGED", label: "Colour, print or pattern changed" },
  { code: "GARMENT_LENGTH_OR_SHAPE", label: "Length or garment shape looks incorrect" },
  { code: "BODY_ALIGNMENT_ISSUE", label: "Garment placement or body alignment is incorrect" },
  { code: "FACE_OR_BODY_CHANGED", label: "My face or body appearance changed unexpectedly" },
  { code: "MISLEADING_FIT_IMPRESSION", label: "The image gives a misleading impression of fit" },
  { code: "LAYERING_ERROR", label: "Layering or garment components incorrectly rendered" },
  { code: "IMAGE_ARTIFACT", label: "Visible generation artifact or distortion" },
  { code: "OTHER", label: "Other issue" },
];

/**
 * ReportTryOnModal Component (Phase 07.8 - Task 7.8.5)
 *
 * Allows shoppers to report inaccurate, distorted, or misleading virtual try-on results.
 * Respects strict privacy boundaries: quality review consent is opt-in and does not permit model training.
 */
export function ReportTryOnModal({
  visible,
  jobId,
  onClose,
  onSubmit,
}: ReportTryOnModalProps) {
  const [selectedReason, setSelectedReason] = useState<FeedbackReasonCode>("GARMENT_LOOKS_DIFFERENT");
  const [details, setDetails] = useState("");
  const [includeInReview, setIncludeInReview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      setErrorMessage(null);
      await onSubmit({
        jobId,
        reasonCode: selectedReason,
        details: details.trim() || undefined,
        includeInQualityReview: includeInReview,
      });
      onClose();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to record feedback. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.modalCard} accessible={true} role="dialog" accessibilityViewIsModal={true}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Report a problem with this try-on</Text>
            <TouchableOpacity onPress={onClose} accessibilityRole="button" accessibilityLabel="Close report dialog">
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollArea}>
            <Text style={styles.sectionLabel}>What went wrong?</Text>

            <View style={styles.optionsList}>
              {REASON_OPTIONS.map((opt) => {
                const isSelected = selectedReason === opt.code;
                return (
                  <TouchableOpacity
                    key={opt.code}
                    style={[styles.optionRow, isSelected && styles.optionRowSelected]}
                    onPress={() => setSelectedReason(opt.code)}
                    accessibilityRole="radio"
                    accessibilityState={{ selected: isSelected }}
                  >
                    <View style={[styles.radioCircle, isSelected && styles.radioCircleSelected]} />
                    <Text style={[styles.optionText, isSelected && styles.optionTextSelected]}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <Text style={styles.sectionLabel}>Additional details (optional)</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Describe the issue with the image..."
              placeholderTextColor="#98A2B3"
              multiline={true}
              numberOfLines={3}
              maxLength={2000}
              value={details}
              onChangeText={setDetails}
            />

            <View style={styles.consentCard}>
              <View style={styles.consentTextColumn}>
                <Text style={styles.consentTitle}>Include in internal quality review</Text>
                <Text style={styles.consentDescription}>
                  Allow FashX team to inspect this generated image for bug fixes. Does NOT authorize AI model training.
                </Text>
              </View>
              <Switch
                value={includeInReview}
                onValueChange={setIncludeInReview}
                trackColor={{ false: "#D0D5DD", true: "#027A48" }}
              />
            </View>

            {errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity
              style={styles.cancelBtn}
              onPress={onClose}
              disabled={submitting}
              accessibilityRole="button"
            >
              <Text style={styles.cancelBtnText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
              onPress={handleSubmit}
              disabled={submitting}
              accessibilityRole="button"
            >
              {submitting ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={styles.submitBtnText}>Submit Report</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalCard: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    maxHeight: "85%",
    padding: 20,
    gap: 16,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1D2939",
  },
  closeButton: {
    fontSize: 18,
    color: "#667085",
    padding: 4,
  },
  scrollArea: {
    maxHeight: 460,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#344054",
    marginBottom: 8,
    marginTop: 10,
  },
  optionsList: {
    gap: 8,
  },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#EAECF0",
    backgroundColor: "#FFFFFF",
    gap: 10,
  },
  optionRowSelected: {
    borderColor: "#027A48",
    backgroundColor: "#F6FEF9",
  },
  radioCircle: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: "#D0D5DD",
  },
  radioCircleSelected: {
    borderColor: "#027A48",
    backgroundColor: "#027A48",
  },
  optionText: {
    fontSize: 13,
    color: "#344054",
    flex: 1,
  },
  optionTextSelected: {
    fontWeight: "600",
    color: "#027A48",
  },
  textInput: {
    borderWidth: 1,
    borderColor: "#D0D5DD",
    borderRadius: 8,
    padding: 10,
    fontSize: 13,
    color: "#1D2939",
    textAlignVertical: "top",
    minHeight: 70,
  },
  consentCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#F9FAFB",
    padding: 12,
    borderRadius: 8,
    marginTop: 14,
    gap: 12,
  },
  consentTextColumn: {
    flex: 1,
  },
  consentTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: "#1D2939",
  },
  consentDescription: {
    fontSize: 11,
    color: "#667085",
    marginTop: 2,
  },
  errorText: {
    fontSize: 12,
    color: "#D92D20",
    marginTop: 8,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 12,
    marginTop: 12,
  },
  cancelBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  cancelBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#475467",
  },
  submitBtn: {
    backgroundColor: "#1D2939",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFFFFF",
  },
});
