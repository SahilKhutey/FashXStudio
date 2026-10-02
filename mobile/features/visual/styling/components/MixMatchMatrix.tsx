import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from "react-native";
import { CandidateItemContract, MixMatchContract, OutfitItemContract } from "../types";

interface MixMatchMatrixProps {
  matrix: MixMatchContract;
  onSelectCandidate: (slotId: string, productId: string) => void;
  currency?: string;
  testID?: string;
}

export const MixMatchMatrix: React.FC<MixMatchMatrixProps> = ({
  matrix,
  onSelectCandidate,
  currency = "INR",
  testID = "mix-match-matrix",
}) => {
  const isCurrentlySelected = (slotId: string, productId: string) => {
    return matrix.current_items.some(
      (item) => item.slot_id === slotId && item.product_id === productId
    );
  };

  const renderSlotCandidateRail = (candidateGroup: CandidateItemContract) => {
    return (
      <View key={candidateGroup.slot_id} style={styles.railContainer}>
        <View style={styles.railHeader}>
          <Text style={styles.railCategory}>{candidateGroup.category.toUpperCase()}</Text>
          <Text style={styles.candidateCount}>
            {candidateGroup.products.length} alternatives
          </Text>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.railScroll}
        >
          {candidateGroup.products.map((product: OutfitItemContract) => {
            const isSelected = isCurrentlySelected(candidateGroup.slot_id, product.product_id);
            return (
              <TouchableOpacity
                key={product.product_id}
                testID={`candidate-${candidateGroup.slot_id}-${product.product_id}`}
                activeOpacity={0.8}
                onPress={() => onSelectCandidate(candidateGroup.slot_id, product.product_id)}
                style={[styles.candidateCard, isSelected && styles.selectedCandidateCard]}
              >
                <Image
                  source={{ uri: product.image_uri }}
                  style={styles.candidateImage}
                  resizeMode="cover"
                />
                <View style={styles.candidateInfo}>
                  <Text style={styles.candidateBrand} numberOfLines={1}>
                    {product.brand}
                  </Text>
                  <Text style={styles.candidateTitle} numberOfLines={1}>
                    {product.title}
                  </Text>
                  <Text style={styles.candidatePrice}>
                    {currency === "INR" ? "₹" : "$"}
                    {product.price.toLocaleString()}
                  </Text>
                </View>
                {isSelected && (
                  <View style={styles.activeCheckBadge}>
                    <Text style={styles.activeCheckText}>✓ Active</Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    );
  };

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        {matrix.candidates_by_slot.map(renderSlotCandidateRail)}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  content: {
    paddingVertical: 12,
  },
  railContainer: {
    marginBottom: 20,
  },
  railHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  railCategory: {
    fontSize: 13,
    fontWeight: "700",
    color: "#222222",
    letterSpacing: 0.8,
  },
  candidateCount: {
    fontSize: 12,
    color: "#777777",
  },
  railScroll: {
    paddingHorizontal: 16,
    gap: 12,
  },
  candidateCard: {
    width: 130,
    backgroundColor: "#ffffff",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    overflow: "hidden",
  },
  selectedCandidateCard: {
    borderColor: "#111111",
    borderWidth: 2,
  },
  candidateImage: {
    width: "100%",
    height: 140,
    backgroundColor: "#f3f4f6",
  },
  candidateInfo: {
    padding: 8,
  },
  candidateBrand: {
    fontSize: 10,
    fontWeight: "700",
    color: "#6b7280",
    textTransform: "uppercase",
  },
  candidateTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
    marginTop: 2,
  },
  candidatePrice: {
    fontSize: 12,
    fontWeight: "700",
    color: "#111111",
    marginTop: 4,
  },
  activeCheckBadge: {
    position: "absolute",
    top: 6,
    right: 6,
    backgroundColor: "#111111",
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  activeCheckText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "700",
  },
});
