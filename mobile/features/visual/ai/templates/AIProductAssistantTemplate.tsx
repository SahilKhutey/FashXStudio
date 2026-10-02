import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIProductAssistantTemplateSpecContract } from "../types";
import { AIPromptInput } from "../components/AIPromptInput";

interface AIProductAssistantTemplateProps {
  data: AIProductAssistantTemplateSpecContract;
  onSubmitPrompt: (prompt: string) => void;
  onPressLook?: (lookId: string) => void;
  onPressProduct?: (productId: string) => void;
  testID?: string;
}

export const AIProductAssistantTemplate: React.FC<AIProductAssistantTemplateProps> = ({
  data,
  onSubmitPrompt,
  onPressLook,
  onPressProduct,
  testID = "ai-product-assistant-screen",
}) => {
  const { product, product_facts, ai_guidance, frequently_asked, styling_suggestions, similar_products } = data;

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTag}>PRODUCT INTELLIGENCE</Text>
          <Text style={styles.title}>{product.title}</Text>
          {product.subtitle && <Text style={styles.subtitle}>{product.subtitle}</Text>}
        </View>

        {/* Section 12.16: Authoritative Product Facts (Catalog Truth) */}
        {product_facts && Object.keys(product_facts).length > 0 && (
          <View style={styles.factsCard}>
            <View style={styles.factsHeaderRow}>
              <Text style={styles.factsHeader}>AUTHORITATIVE PRODUCT FACTS</Text>
              <Text style={styles.verifiedBadge}>✓ CATALOG VERIFIED</Text>
            </View>
            <View style={styles.factsGrid}>
              {Object.entries(product_facts).map(([key, val]) => (
                <View key={key} style={styles.factRow}>
                  <Text style={styles.factKey}>{key}:</Text>
                  <Text style={styles.factVal}>{val}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* AI Guidance Box (Clearly Labeled Recommendation) */}
        <View style={styles.guidanceBox}>
          <Text style={styles.guidanceTag}>AI STYLING GUIDANCE</Text>
          <Text style={styles.guidanceText}>{ai_guidance}</Text>
        </View>

        {/* Styling Suggestions Rail */}
        {styling_suggestions && styling_suggestions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>STYLED ENSEMBLES</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
              {styling_suggestions.map((l) => (
                <TouchableOpacity
                  key={l.id}
                  testID={`styling-look-${l.id}`}
                  style={styles.lookCard}
                  onPress={() => onPressLook?.(l.id)}
                >
                  <View style={styles.cardPlaceholder}>
                    <Text style={styles.cardPlaceholderText}>LOOK</Text>
                  </View>
                  <Text style={styles.cardTitle} numberOfLines={1}>{l.title}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Similar Products Rail */}
        {similar_products && similar_products.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>SIMILAR CATALOG PIECES</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
              {similar_products.map((p) => (
                <TouchableOpacity
                  key={p.id}
                  testID={`similar-prod-${p.id}`}
                  style={styles.lookCard}
                  onPress={() => onPressProduct?.(p.id)}
                >
                  <View style={styles.cardPlaceholder}>
                    <Text style={styles.cardPlaceholderText}>PRODUCT</Text>
                  </View>
                  <Text style={styles.cardTitle} numberOfLines={1}>{p.title}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </ScrollView>

      <AIPromptInput
        placeholder="Ask about sizing, fit, or styling..."
        quickPrompts={frequently_asked}
        onSubmit={onSubmitPrompt}
      />
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
    color: "#8E8E93",
    letterSpacing: 1,
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  subtitle: {
    fontSize: 13,
    color: "#636366",
    marginTop: 2,
  },
  factsCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 14,
    marginBottom: 16,
  },
  factsHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
    paddingBottom: 6,
  },
  factsHeader: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
  },
  verifiedBadge: {
    fontSize: 9,
    fontWeight: "700",
    color: "#34C759",
    letterSpacing: 0.5,
  },
  factsGrid: {
    gap: 6,
  },
  factRow: {
    flexDirection: "row",
  },
  factKey: {
    width: 100,
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  factVal: {
    flex: 1,
    fontSize: 12,
    color: "#48484A",
  },
  guidanceBox: {
    backgroundColor: "#F9F9FB",
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: "#5856D6",
    padding: 14,
    marginBottom: 20,
  },
  guidanceTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  guidanceText: {
    fontSize: 13,
    color: "#1C1C1E",
    lineHeight: 18,
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
  lookCard: {
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
  cardPlaceholderText: {
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
