import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIStyleAssistantTemplateSpecContract } from "../types";
import { AIExplanationCard } from "../components/AIExplanationCard";

interface AIStyleAssistantTemplateProps {
  data: AIStyleAssistantTemplateSpecContract;
  onPressLook?: (lookId: string) => void;
  onPressProduct?: (productId: string) => void;
  onPressOpenStudio?: (styleId: string) => void;
  testID?: string;
}

export const AIStyleAssistantTemplate: React.FC<AIStyleAssistantTemplateProps> = ({
  data,
  onPressLook,
  onPressProduct,
  onPressOpenStudio,
  testID = "ai-style-assistant-screen",
}) => {
  const { recommended_style, why_it_fits, matching_looks, suggested_products } = data;

  return (
    <ScrollView
      testID={testID}
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.headerTag}>RECOMMENDED AESTHETIC DIRECTION</Text>
        <Text style={styles.title}>{recommended_style.title}</Text>
        {recommended_style.subtitle && (
          <Text style={styles.subtitle}>{recommended_style.subtitle}</Text>
        )}
      </View>

      {/* Transparent Explanation Card */}
      <AIExplanationCard explanation={why_it_fits} />

      {/* Quick Studio Trigger */}
      {onPressOpenStudio && (
        <TouchableOpacity
          testID="style-open-studio-btn"
          style={styles.studioButton}
          onPress={() => onPressOpenStudio(recommended_style.id)}
        >
          <Text style={styles.studioButtonText}>Open in Outfit Studio →</Text>
        </TouchableOpacity>
      )}

      {/* Matching Looks Rail */}
      {matching_looks && matching_looks.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>CURATED STYLE LOOKS</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {matching_looks.map((l) => (
              <TouchableOpacity
                key={l.id}
                testID={`style-look-${l.id}`}
                style={styles.card}
                onPress={() => onPressLook?.(l.id)}
              >
                <View style={styles.cardPlaceholder}>
                  <Text style={styles.cardTag}>LOOK</Text>
                </View>
                <Text style={styles.cardTitle} numberOfLines={1}>{l.title}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Suggested Products Rail */}
      {suggested_products && suggested_products.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PIECES IN THIS STYLE</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
            {suggested_products.map((p) => (
              <TouchableOpacity
                key={p.id}
                testID={`style-product-${p.id}`}
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
    fontSize: 24,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
  },
  subtitle: {
    fontSize: 13,
    color: "#636366",
    marginTop: 4,
  },
  studioButton: {
    backgroundColor: "#1C1C1E",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 24,
  },
  studioButtonText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
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
