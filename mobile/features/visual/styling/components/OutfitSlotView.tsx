import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { OutfitSlotContract, SlotCategory, SlotState } from "../types";

interface OutfitSlotViewProps {
  slot: OutfitSlotContract;
  isActive?: boolean;
  onSelectSlot?: (slotId: string) => void;
  onAddItem?: (slotId: string) => void;
  onReplaceItem?: (slotId: string) => void;
  onRemoveItem?: (slotId: string) => void;
  currency?: string;
  testID?: string;
}

export const OutfitSlotView: React.FC<OutfitSlotViewProps> = ({
  slot,
  isActive = false,
  onSelectSlot,
  onAddItem,
  onReplaceItem,
  onRemoveItem,
  currency = "INR",
  testID = `outfit-slot-${slot.id}`,
}) => {
  const getCategoryIcon = (category: SlotCategory): string => {
    switch (category) {
      case "outerwear":
        return "🧥";
      case "top":
        return "👕";
      case "bottom":
        return "👖";
      case "footwear":
        return "👟";
      case "bag":
        return "👜";
      case "accessory":
        return "🕶️";
      default:
        return "✨";
    }
  };

  const isFilled = slot.item !== null && slot.item !== undefined;

  return (
    <TouchableOpacity
      testID={testID}
      activeOpacity={0.85}
      onPress={() => onSelectSlot?.(slot.id)}
      style={[
        styles.slotCard,
        isActive && styles.activeCard,
        slot.state === "locked" && styles.lockedCard,
      ]}
    >
      <View style={styles.headerRow}>
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryIcon}>{getCategoryIcon(slot.category)}</Text>
          <Text style={styles.categoryName}>{slot.name.toUpperCase()}</Text>
        </View>
        {slot.required && !isFilled && (
          <Text style={styles.requiredTag}>REQUIRED</Text>
        )}
      </View>

      {isFilled && slot.item ? (
        <View style={styles.filledContent}>
          <Image
            source={{ uri: slot.item.image_uri }}
            style={styles.itemImage}
            resizeMode="cover"
          />
          <View style={styles.itemDetails}>
            <Text style={styles.itemBrand}>{slot.item.brand.toUpperCase()}</Text>
            <Text style={styles.itemTitle} numberOfLines={2}>
              {slot.item.title}
            </Text>
            <Text style={styles.itemPrice}>
              {currency === "INR" ? "₹" : "$"}
              {slot.item.price.toLocaleString()}
            </Text>
            {slot.item.selected_variants && Object.keys(slot.item.selected_variants).length > 0 && (
              <View style={styles.variantsRow}>
                {Object.entries(slot.item.selected_variants).map(([k, v]) => (
                  <Text key={k} style={styles.variantChip}>
                    {k}: {v}
                  </Text>
                ))}
              </View>
            )}
          </View>
          <View style={styles.actionsColumn}>
            <TouchableOpacity
              testID={`${testID}-replace`}
              style={styles.actionButton}
              onPress={() => onReplaceItem?.(slot.id)}
            >
              <Text style={styles.actionButtonText}>Swap</Text>
            </TouchableOpacity>
            <TouchableOpacity
              testID={`${testID}-remove`}
              style={[styles.actionButton, styles.removeButton]}
              onPress={() => onRemoveItem?.(slot.id)}
            >
              <Text style={styles.removeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={styles.emptySlot}>
          <Text style={styles.emptyText}>Empty {slot.name}</Text>
          <TouchableOpacity
            testID={`${testID}-add`}
            style={styles.addButton}
            onPress={() => onAddItem?.(slot.id)}
          >
            <Text style={styles.addButtonText}>+ Add {slot.name}</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  slotCard: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e0e0e0",
    padding: 12,
    marginBottom: 10,
  },
  activeCard: {
    borderColor: "#111111",
    borderWidth: 2,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  lockedCard: {
    backgroundColor: "#f9f9f9",
    opacity: 0.7,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  categoryBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  categoryIcon: {
    fontSize: 14,
  },
  categoryName: {
    fontSize: 12,
    fontWeight: "700",
    color: "#666666",
    letterSpacing: 0.8,
  },
  requiredTag: {
    fontSize: 10,
    fontWeight: "700",
    color: "#d83b01",
    letterSpacing: 0.5,
  },
  filledContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  itemImage: {
    width: 64,
    height: 64,
    borderRadius: 8,
    backgroundColor: "#f0f0f0",
  },
  itemDetails: {
    flex: 1,
  },
  itemBrand: {
    fontSize: 11,
    fontWeight: "700",
    color: "#888888",
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111111",
    marginTop: 2,
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111111",
    marginTop: 4,
  },
  variantsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 4,
    marginTop: 4,
  },
  variantChip: {
    fontSize: 10,
    color: "#555555",
    backgroundColor: "#f2f2f2",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  actionsColumn: {
    alignItems: "flex-end",
    gap: 6,
  },
  actionButton: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: "#f0f0f0",
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#333333",
  },
  removeButton: {
    backgroundColor: "#fee2e2",
  },
  removeButtonText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#b91c1c",
  },
  emptySlot: {
    paddingVertical: 14,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderStyle: "dashed",
    borderRadius: 8,
    backgroundColor: "#fafafa",
  },
  emptyText: {
    fontSize: 13,
    color: "#9ca3af",
    marginBottom: 6,
  },
  addButton: {
    backgroundColor: "#111111",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  addButtonText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "600",
  },
});
