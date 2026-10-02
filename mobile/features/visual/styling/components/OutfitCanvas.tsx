import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { OutfitContract } from "../types";
import { OutfitSlotView } from "./OutfitSlotView";

interface OutfitCanvasProps {
  outfit: OutfitContract;
  activeSlotId?: string | null;
  onSelectSlot?: (slotId: string) => void;
  onAddItem?: (slotId: string) => void;
  onReplaceItem?: (slotId: string) => void;
  onRemoveItem?: (slotId: string) => void;
  onMixMatch?: () => void;
  onPreview?: () => void;
  onSaveOutfit?: () => void;
  onShopOutfit?: () => void;
  currency?: string;
  testID?: string;
}

export const OutfitCanvas: React.FC<OutfitCanvasProps> = ({
  outfit,
  activeSlotId,
  onSelectSlot,
  onAddItem,
  onReplaceItem,
  onRemoveItem,
  onMixMatch,
  onPreview,
  onSaveOutfit,
  onShopOutfit,
  currency = "INR",
  testID = "outfit-canvas",
}) => {
  const sortedSlots = [...outfit.slots].sort((a, b) => a.position - b.position);
  const filledCount = outfit.slots.filter((s) => s.item !== null && s.item !== undefined).length;
  const totalSlots = outfit.slots.length;

  return (
    <View testID={testID} style={styles.container}>
      {/* Canvas Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.styleName}>{outfit.style_name.toUpperCase()}</Text>
          <Text style={styles.outfitName}>{outfit.name}</Text>
        </View>
        <View
          style={[
            styles.statusBadge,
            outfit.is_complete ? styles.completeBadge : styles.incompleteBadge,
          ]}
        >
          <Text
            style={[
              styles.statusText,
              outfit.is_complete ? styles.completeText : styles.incompleteText,
            ]}
          >
            {outfit.is_complete ? "Complete" : `${filledCount}/${totalSlots} Slots`}
          </Text>
        </View>
      </View>

      {/* Slots List */}
      <ScrollView
        style={styles.slotsScroll}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.slotsContent}
      >
        {sortedSlots.map((slot) => (
          <OutfitSlotView
            key={slot.id}
            slot={slot}
            isActive={slot.id === activeSlotId}
            onSelectSlot={onSelectSlot}
            onAddItem={onAddItem}
            onReplaceItem={onReplaceItem}
            onRemoveItem={onRemoveItem}
            currency={currency}
          />
        ))}
      </ScrollView>

      {/* Canvas Summary & Action Bar */}
      <View style={styles.bottomBar}>
        <View style={styles.priceContainer}>
          <Text style={styles.priceLabel}>TOTAL ({filledCount} items)</Text>
          <Text style={styles.priceValue}>
            {currency === "INR" ? "₹" : "$"}
            {outfit.total_price.toLocaleString()}
          </Text>
        </View>

        <View style={styles.actionButtonsRow}>
          {onMixMatch && (
            <TouchableOpacity
              testID="canvas-mix-match-btn"
              style={styles.secondaryBtn}
              onPress={onMixMatch}
            >
              <Text style={styles.secondaryBtnText}>Mix & Match</Text>
            </TouchableOpacity>
          )}

          {onPreview && (
            <TouchableOpacity
              testID="canvas-preview-btn"
              style={styles.secondaryBtn}
              onPress={onPreview}
            >
              <Text style={styles.secondaryBtnText}>Preview</Text>
            </TouchableOpacity>
          )}

          {onSaveOutfit && (
            <TouchableOpacity
              testID="canvas-save-btn"
              style={styles.secondaryBtn}
              onPress={onSaveOutfit}
            >
              <Text style={styles.secondaryBtnText}>Save</Text>
            </TouchableOpacity>
          )}

          {onShopOutfit && (
            <TouchableOpacity
              testID="canvas-shop-btn"
              style={styles.primaryBtn}
              onPress={onShopOutfit}
            >
              <Text style={styles.primaryBtnText}>Shop Look</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8f9fa",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  styleName: {
    fontSize: 11,
    fontWeight: "700",
    color: "#888888",
    letterSpacing: 1,
  },
  outfitName: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  completeBadge: {
    backgroundColor: "#e6f4ea",
  },
  incompleteBadge: {
    backgroundColor: "#fef3c7",
  },
  statusText: {
    fontSize: 12,
    fontWeight: "700",
  },
  completeText: {
    color: "#137333",
  },
  incompleteText: {
    color: "#b45309",
  },
  slotsScroll: {
    flex: 1,
  },
  slotsContent: {
    padding: 16,
    paddingBottom: 24,
  },
  bottomBar: {
    backgroundColor: "#ffffff",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    flexDirection: "column",
    gap: 10,
  },
  priceContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
  },
  priceLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#6b7280",
    letterSpacing: 0.5,
  },
  priceValue: {
    fontSize: 20,
    fontWeight: "800",
    color: "#111111",
  },
  actionButtonsRow: {
    flexDirection: "row",
    gap: 8,
  },
  secondaryBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#d1d5db",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ffffff",
  },
  secondaryBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#374151",
  },
  primaryBtn: {
    flex: 1.4,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: "#111111",
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#ffffff",
  },
});
