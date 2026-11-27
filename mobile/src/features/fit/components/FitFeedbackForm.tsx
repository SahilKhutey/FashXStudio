import React, { useState } from "react";
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import type { FitFeedbackCreateRequest, FitFeedbackReason } from "../types/fit";

export interface FitFeedbackFormProps {
  recommendationId: string;
  submitting?: boolean;
  submitted?: boolean;
  onSubmit: (recommendationId: string, payload: FitFeedbackCreateRequest) => Promise<unknown> | void;
}

const QUICK_REASONS: { code: FitFeedbackReason; label: string }[] = [
  { code: "FIT_TOO_TIGHT", label: "Too tight" },
  { code: "FIT_TOO_LOOSE", label: "Too loose" },
  { code: "SIZE_CHART_INACCURATE", label: "Chart inaccurate" },
  { code: "RECOMMENDATION_UNHELPFUL", label: "Unhelpful" },
];

export function FitFeedbackForm({
  recommendationId,
  submitting = false,
  submitted = false,
  onSubmit,
}: FitFeedbackFormProps) {
  const [selectedReason, setSelectedReason] = useState<FitFeedbackReason>("RECOMMENDATION_UNHELPFUL");
  const [triedOn, setTriedOn] = useState<boolean>(false);
  const [comment, setComment] = useState<string>("");

  if (submitted) {
    return (
      <View style={styles.submittedBox} testID="fit-feedback-submitted">
        <Text style={styles.submittedText}>
          Thank you — your fit guidance feedback has been recorded for quality review.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container} testID="fit-feedback-form">
      <Text style={styles.heading}>Was this size guidance helpful?</Text>
      <View style={styles.chipRow}>
        {QUICK_REASONS.map((item) => {
          const active = selectedReason === item.code;
          return (
            <TouchableOpacity
              key={item.code}
              accessibilityRole="button"
              style={[styles.chip, active && styles.chipActive]}
              onPress={() => setSelectedReason(item.code)}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{item.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <TouchableOpacity
        accessibilityRole="button"
        style={styles.toggleRow}
        onPress={() => setTriedOn((prev) => !prev)}
      >
        <Text style={styles.toggleText}>
          {triedOn ? "[x] Physically tried garment on" : "[ ] Did not try physical garment on yet"}
        </Text>
      </TouchableOpacity>

      <TextInput
        style={styles.input}
        placeholder="Optional fit notes..."
        value={comment}
        onChangeText={setComment}
        multiline
      />

      <TouchableOpacity
        accessibilityRole="button"
        disabled={submitting}
        style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
        onPress={() =>
          onSubmit(recommendationId, {
            reason: selectedReason,
            purchase_status: triedOn ? "PURCHASED" : "UNKNOWN",
            tried_on: triedOn,
            comment: comment.trim() || null,
          })
        }
      >
        <Text style={styles.submitBtnText}>
          {submitting ? "Submitting..." : "Submit feedback"}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  heading: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 6,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  chip: {
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: "#FFFFFF",
  },
  chipActive: {
    borderColor: "#111827",
    backgroundColor: "#111827",
  },
  chipText: {
    fontSize: 12,
    color: "#374151",
  },
  chipTextActive: {
    color: "#FFFFFF",
  },
  toggleRow: {
    marginTop: 8,
    paddingVertical: 4,
  },
  toggleText: {
    fontSize: 12,
    color: "#374151",
  },
  input: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 6,
    fontSize: 12,
    minHeight: 44,
    color: "#111827",
  },
  submitBtn: {
    marginTop: 8,
    backgroundColor: "#111827",
    borderRadius: 6,
    paddingVertical: 8,
    alignItems: "center",
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  submittedBox: {
    marginTop: 12,
    padding: 8,
    borderRadius: 6,
    backgroundColor: "#ECFDF5",
  },
  submittedText: {
    fontSize: 12,
    color: "#065F46",
  },
});
