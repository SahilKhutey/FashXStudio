import React from "react";
import { StyleSheet, Text, View } from "react-native";

export interface FitExplanationProps {
  summary: string;
  details?: string[];
  nextActions?: string[];
}

export function FitExplanation({
  summary,
  details = [],
  nextActions = [],
}: FitExplanationProps) {
  return (
    <View style={styles.container} testID="fit-explanation">
      <Text style={styles.heading}>Why this size is suggested</Text>
      <Text style={styles.summary}>{summary}</Text>
      {details.map((line, idx) => (
        <Text key={`${idx}-${line}`} style={styles.bullet}>
          • {line}
        </Text>
      ))}
      {nextActions.length > 0 && (
        <View style={styles.actionBox}>
          <Text style={styles.actionHeading}>Recommended next steps</Text>
          {nextActions.map((act, idx) => (
            <Text key={`${idx}-${act}`} style={styles.actionText}>
              • {act}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
  },
  heading: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  summary: {
    fontSize: 13,
    color: "#1F2937",
    lineHeight: 18,
    marginBottom: 4,
  },
  bullet: {
    fontSize: 12,
    color: "#4B5563",
    lineHeight: 17,
  },
  actionBox: {
    marginTop: 8,
    padding: 8,
    backgroundColor: "#EFF6FF",
    borderRadius: 6,
  },
  actionHeading: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1E40AF",
    marginBottom: 2,
  },
  actionText: {
    fontSize: 12,
    color: "#1E3A8A",
  },
});
