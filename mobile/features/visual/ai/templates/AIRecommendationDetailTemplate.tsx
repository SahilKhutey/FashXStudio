import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIRecommendationDetailTemplateSpecContract } from "../types";
import { AIExplanationCard } from "../components/AIExplanationCard";
import { AIContextChips } from "../components/AIContextChips";

interface AIRecommendationDetailTemplateProps {
  data: AIRecommendationDetailTemplateSpecContract;
  onPressAction?: (actionId: string, targetId?: string | null) => void;
  onPressProduct?: (productId: string) => void;
  onPressAlternative?: (altId: string) => void;
  testID?: string;
}

export const AIRecommendationDetailTemplate: React.FC<AIRecommendationDetailTemplateProps> = ({
  data,
  onPressAction,
  onPressProduct,
  onPressAlternative,
  testID = "ai-recommendation-detail-screen",
}) => {
  const { recommendation, context_used, supporting_products, alternatives } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.headerTag}>RECOMMENDATION DEEP DIVE</Text>
        <Text style={styles.title}>{recommendation.title}</Text>
      </View>

      {context_used && context_used.length > 0 && (
        <View style={styles.contextContainer}>
          <AIContextChips contextItems={context_used} />
        </View>
      )}

      {/* Explanation Breakdown */}
      <AIExplanationCard explanation={recommendation.explanation} />

      {/* Action Triggers */}
      {recommendation.actions && recommendation.actions.length > 0 && (
        <View style={styles.actionsGrid}>
          {recommendation.actions.map((act) => (
            <TouchableOpacity
              key={act.action_id}
              testID={`rec-detail-action-${act.action_id}`}
              style={styles.actionBtn}
              onPress={() => onPressAction?.(act.action_id, act.target_id)}
            >
              <Text style={styles.actionBtnText}>{act.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Supporting Products Rail */}
      {supporting_products && supporting_products.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>SUPPORTING PRODUCTS</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {supporting_products.map((p) => (
              <TouchableOpacity
                key={p.id}
                testID={`rec-support-prod-${p.id}`}
                style={styles.card}
                onPress={() => onPressProduct?.(p.id)}
              >
                <View style={styles.cardPlaceholder}>
                  <Text style={styles.cardTag}>PRODUCT</Text>
                </View>
                <Text style={styles.cardTitle} numberOfLines={1}>{p.title}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Alternatives Rail */}
      {alternatives && alternatives.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>EXPLORE ALTERNATIVES</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {alternatives.map((alt) => (
              <TouchableOpacity
                key={alt.id}
                testID={`rec-alt-${alt.id}`}
                style={styles.card}
                onPress={() => onPressAlternative?.(alt.id)}
              >
                <View style={styles.cardPlaceholder}>
                  <Text style={styles.cardTag}>ALT</Text>
                </View>
                <Text style={styles.cardTitle} numberOfLines={1}>{alt.title}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </ScrollView>
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
  contextContainer: {
    marginBottom: 16,
  },
  actionsGrid: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 20,
  },
  actionBtn: {
    flex: 1,
    backgroundColor: "#1C1C1E",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  actionBtnText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.1,
    marginBottom: 10,
  },
  rail: {
    gap: 12,
  },
  card: {
    width: 130,
  },
  cardPlaceholder: {
    height: 140,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 6,
  },
  cardTag: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
