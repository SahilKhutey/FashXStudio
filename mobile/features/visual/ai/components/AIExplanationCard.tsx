import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { AIExplanationContract } from "../types";

interface AIExplanationCardProps {
  explanation: AIExplanationContract;
  testID?: string;
}

export const AIExplanationCard: React.FC<AIExplanationCardProps> = ({
  explanation,
  testID = "ai-explanation-card-component",
}) => {
  const { primary_reason, detailed_narrative, matching_factors, context_used } = explanation;

  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.headerTag}>TRANSPARENT REASONING</Text>
        <Text style={styles.title}>{primary_reason}</Text>
      </View>

      <Text style={styles.narrative}>{detailed_narrative}</Text>

      {/* Contributing Factors */}
      {matching_factors && matching_factors.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>MATCHING ATTRIBUTES</Text>
          {matching_factors.map((factor, idx) => (
            <View key={idx} style={styles.factorRow}>
              <Text style={styles.factorCheck}>✓</Text>
              <Text style={styles.factorName}>{factor.factor_name}:</Text>
              <Text style={styles.factorValue}>{factor.factor_value}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Context Applied */}
      {context_used && context_used.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>CONTEXT APPLIED</Text>
          <View style={styles.contextPillsRow}>
            {context_used.map((ctx, idx) => (
              <View key={idx} style={styles.contextPill}>
                <Text style={styles.contextPillText}>{ctx}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 16,
    marginBottom: 16,
  },
  header: {
    marginBottom: 10,
  },
  headerTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1C1C1E",
    lineHeight: 22,
  },
  narrative: {
    fontSize: 13,
    color: "#48484A",
    lineHeight: 18,
    marginBottom: 16,
  },
  section: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  sectionTitle: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  factorRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  factorCheck: {
    fontSize: 12,
    fontWeight: "700",
    color: "#34C759",
    marginRight: 6,
  },
  factorName: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
    marginRight: 4,
  },
  factorValue: {
    fontSize: 12,
    color: "#636366",
  },
  contextPillsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  contextPill: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  contextPillText: {
    fontSize: 11,
    color: "#48484A",
  },
});
