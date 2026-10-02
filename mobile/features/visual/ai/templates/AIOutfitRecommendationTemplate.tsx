import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { AIOutfitRecommendationTemplateSpecContract } from "../types";
import { AIExplanationCard } from "../components/AIExplanationCard";

interface AIOutfitRecommendationTemplateProps {
  data: AIOutfitRecommendationTemplateSpecContract;
  onPressEdit?: (lookId: string) => void;
  onPressSave?: (lookId: string) => void;
  onPressShop?: (lookId: string) => void;
  onPressItem?: (itemId: string) => void;
  testID?: string;
}

export const AIOutfitRecommendationTemplate: React.FC<AIOutfitRecommendationTemplateProps> = ({
  data,
  onPressEdit,
  onPressSave,
  onPressShop,
  onPressItem,
  testID = "ai-outfit-recommendation-screen",
}) => {
  const { recommended_look, explanation, constituent_items, alternatives, can_edit } = data;

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={styles.heroImagePlaceholder}>
          <Text style={styles.heroTag}>RECOMMENDED ENSEMBLE</Text>
        </View>

        <View style={styles.header}>
          <Text style={styles.title}>{recommended_look.title}</Text>
          {recommended_look.subtitle && (
            <Text style={styles.subtitle}>{recommended_look.subtitle}</Text>
          )}
        </View>

        {/* Explainability Breakdown */}
        <AIExplanationCard explanation={explanation} />

        {/* Constituent Garments */}
        {constituent_items && constituent_items.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>CONSTITUENT PIECES ({constituent_items.length})</Text>
            {constituent_items.map((item) => (
              <TouchableOpacity
                key={item.id}
                testID={`outfit-piece-${item.id}`}
                style={styles.pieceRow}
                onPress={() => onPressItem?.(item.id)}
              >
                <View style={styles.pieceThumb}>
                  <Text style={styles.pieceTag}>{item.media_type.toUpperCase()}</Text>
                </View>
                <View style={styles.pieceInfo}>
                  <Text style={styles.pieceTitle}>{item.title}</Text>
                  {item.subtitle && <Text style={styles.pieceSubtitle}>{item.subtitle}</Text>}
                </View>
                <Text style={styles.pieceArrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Alternative Looks */}
        {alternatives && alternatives.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>ALTERNATIVE DIRECTIONS</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.rail}>
              {alternatives.map((alt) => (
                <TouchableOpacity
                  key={alt.id}
                  testID={`alt-look-${alt.id}`}
                  style={styles.altCard}
                  onPress={() => onPressEdit?.(alt.id)}
                >
                  <View style={styles.altPlaceholder}>
                    <Text style={styles.altTag}>ALT</Text>
                  </View>
                  <Text style={styles.altTitle} numberOfLines={1}>{alt.title}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </ScrollView>

      {/* Sticky Bottom Actions Bar (Section 12.58: User in Control) */}
      <View style={styles.bottomBar}>
        {can_edit && onPressEdit && (
          <TouchableOpacity
            testID="rec-edit-outfit-btn"
            style={styles.editButton}
            onPress={() => onPressEdit(recommended_look.id)}
          >
            <Text style={styles.editButtonText}>Edit Outfit</Text>
          </TouchableOpacity>
        )}

        {onPressSave && (
          <TouchableOpacity
            testID="rec-save-look-btn"
            style={styles.saveButton}
            onPress={() => onPressSave(recommended_look.id)}
          >
            <Text style={styles.saveButtonText}>Save Look</Text>
          </TouchableOpacity>
        )}

        {onPressShop && (
          <TouchableOpacity
            testID="rec-shop-outfit-btn"
            style={styles.shopButton}
            onPress={() => onPressShop(recommended_look.id)}
          >
            <Text style={styles.shopButtonText}>Shop Pieces</Text>
          </TouchableOpacity>
        )}
      </View>
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
    paddingBottom: 100,
  },
  heroImagePlaceholder: {
    height: 220,
    backgroundColor: "#2C2C2E",
    borderRadius: 12,
    justifyContent: "flex-end",
    padding: 12,
    marginBottom: 16,
  },
  heroTag: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
  },
  header: {
    marginBottom: 16,
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
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.1,
    marginBottom: 10,
  },
  pieceRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 10,
    marginBottom: 8,
  },
  pieceThumb: {
    width: 48,
    height: 48,
    backgroundColor: "#F2F2F7",
    borderRadius: 4,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  pieceTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
  },
  pieceInfo: {
    flex: 1,
  },
  pieceTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  pieceSubtitle: {
    fontSize: 11,
    color: "#636366",
  },
  pieceArrow: {
    fontSize: 14,
    color: "#8E8E93",
  },
  rail: {
    gap: 12,
  },
  altCard: {
    width: 120,
  },
  altPlaceholder: {
    height: 120,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 4,
  },
  altTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
  },
  altTitle: {
    fontSize: 11,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#FFFFFF",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
    padding: 16,
    flexDirection: "row",
    gap: 8,
  },
  editButton: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  editButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  saveButton: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  saveButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  shopButton: {
    flex: 1.2,
    backgroundColor: "#1C1C1E",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  shopButtonText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
