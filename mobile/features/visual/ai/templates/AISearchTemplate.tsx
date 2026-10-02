import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AISearchTemplateSpecContract } from "../types";
import { AIPromptInput } from "../components/AIPromptInput";

interface AISearchTemplateProps {
  data: AISearchTemplateSpecContract;
  onSubmitSearch: (query: string) => void;
  onPressResult?: (resultId: string) => void;
  onPressExplainResult?: (resultId: string) => void;
  testID?: string;
}

export const AISearchTemplate: React.FC<AISearchTemplateProps> = ({
  data,
  onSubmitSearch,
  onPressResult,
  onPressExplainResult,
  testID = "ai-search-screen",
}) => {
  const { query, interpreted_style, interpreted_context, interpreted_budget, results, total_results, processing_steps } = data;

  return (
    <View testID={testID} style={styles.container}>
      <AIPromptInput
        placeholder="Find relaxed summer outfits under ₹3,000..."
        onSubmit={onSubmitSearch}
      />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        {/* Intent Interpretation (Section 12.28, 12.29) */}
        {(interpreted_style || interpreted_context || interpreted_budget) && (
          <View style={styles.intentCard}>
            <Text style={styles.intentHeader}>UNDERSTANDING YOUR REQUEST</Text>
            <View style={styles.intentGrid}>
              {interpreted_style && (
                <View style={styles.intentRow}>
                  <Text style={styles.intentLabel}>Style:</Text>
                  <Text style={styles.intentValue}>{interpreted_style}</Text>
                </View>
              )}
              {interpreted_context && (
                <View style={styles.intentRow}>
                  <Text style={styles.intentLabel}>Context:</Text>
                  <Text style={styles.intentValue}>{interpreted_context}</Text>
                </View>
              )}
              {interpreted_budget && (
                <View style={styles.intentRow}>
                  <Text style={styles.intentLabel}>Budget:</Text>
                  <Text style={styles.intentValue}>{interpreted_budget}</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Multi-Stage Observable Steps (Section 12.43) */}
        {processing_steps && processing_steps.length > 0 && (
          <View style={styles.stepsCard}>
            {processing_steps.map((st) => (
              <View key={st.id} style={styles.stepRow}>
                <Text style={styles.stepCheck}>✓</Text>
                <Text style={styles.stepLabel}>{st.label}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Results Grid */}
        <View style={styles.resultsSection}>
          <Text style={styles.resultsCount}>
            {total_results ?? (results?.length || 0)} MATCHING CATALOG ITEMS
          </Text>

          <View style={styles.resultsGrid}>
            {results &&
              results.map((res) => (
                <View key={res.id} style={styles.resultCard}>
                  <TouchableOpacity
                    testID={`search-result-${res.id}`}
                    onPress={() => onPressResult?.(res.id)}
                    activeOpacity={0.85}
                  >
                    <View style={styles.thumbPlaceholder}>
                      <Text style={styles.thumbTag}>{res.media_type.toUpperCase()}</Text>
                    </View>
                    <Text style={styles.resultTitle} numberOfLines={1}>{res.title}</Text>
                    {res.subtitle && (
                      <Text style={styles.resultSubtitle} numberOfLines={1}>{res.subtitle}</Text>
                    )}
                  </TouchableOpacity>

                  {onPressExplainResult && (
                    <TouchableOpacity
                      testID={`why-result-${res.id}`}
                      style={styles.whyBtn}
                      onPress={() => onPressExplainResult(res.id)}
                    >
                      <Text style={styles.whyBtnText}>Why this result? →</Text>
                    </TouchableOpacity>
                  )}
                </View>
              ))}
          </View>
        </View>
      </ScrollView>
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
  intentCard: {
    backgroundColor: "#F9F9FB",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 12,
    marginBottom: 14,
  },
  intentHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  intentGrid: {
    gap: 4,
  },
  intentRow: {
    flexDirection: "row",
  },
  intentLabel: {
    width: 70,
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  intentValue: {
    fontSize: 12,
    color: "#5856D6",
    fontWeight: "600",
  },
  stepsCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 10,
    marginBottom: 16,
    gap: 4,
  },
  stepRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  stepCheck: {
    fontSize: 11,
    color: "#34C759",
    fontWeight: "700",
    marginRight: 6,
  },
  stepLabel: {
    fontSize: 11,
    color: "#636366",
  },
  resultsSection: {
    marginTop: 8,
  },
  resultsCount: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.1,
    marginBottom: 12,
  },
  resultsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  resultCard: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 10,
    marginBottom: 16,
  },
  thumbPlaceholder: {
    height: 140,
    backgroundColor: "#F2F2F7",
    borderRadius: 4,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  thumbTag: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
  },
  resultTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  resultSubtitle: {
    fontSize: 11,
    color: "#636366",
    marginTop: 2,
    marginBottom: 6,
  },
  whyBtn: {
    paddingVertical: 4,
  },
  whyBtnText: {
    fontSize: 11,
    color: "#007AFF",
    fontWeight: "600",
  },
});
