import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from "react-native";
import { OutfitBuilderTemplateSpecContract } from "../types";
import { OutfitCanvas } from "../components/OutfitCanvas";

interface OutfitBuilderTemplateProps {
  data: OutfitBuilderTemplateSpecContract;
  onSelectSlot?: (slotId: string) => void;
  onAddItem?: (slotId: string) => void;
  onReplaceItem?: (slotId: string) => void;
  onRemoveItem?: (slotId: string) => void;
  onResetOutfit?: () => void;
  onMixMatch?: () => void;
  onPreview?: () => void;
  onSaveOutfit?: () => void;
  onShopOutfit?: () => void;
  testID?: string;
}

export const OutfitBuilderTemplate: React.FC<OutfitBuilderTemplateProps> = ({
  data,
  onSelectSlot,
  onAddItem,
  onReplaceItem,
  onRemoveItem,
  onResetOutfit,
  onMixMatch,
  onPreview,
  onSaveOutfit,
  onShopOutfit,
  testID = "outfit-builder-screen",
}) => {
  const isLoading = data.state === "loading" || data.state === "saving";

  return (
    <View testID={testID} style={styles.container}>
      {/* Top Studio Bar */}
      <View style={styles.studioHeader}>
        <View>
          <Text style={styles.studioTitle}>Outfit Studio</Text>
          <Text style={styles.studioSubtitle}>Interactive Wardrobe Canvas</Text>
        </View>

        <View style={styles.topActionsRow}>
          {isLoading && <ActivityIndicator size="small" color="#111111" />}
          {onResetOutfit && (
            <TouchableOpacity
              testID="reset-slots-btn"
              style={styles.resetButton}
              onPress={onResetOutfit}
            >
              <Text style={styles.resetButtonText}>Reset</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Main Canvas */}
      <OutfitCanvas
        outfit={data.outfit}
        activeSlotId={data.active_slot_id}
        onSelectSlot={onSelectSlot}
        onAddItem={onAddItem}
        onReplaceItem={onReplaceItem}
        onRemoveItem={onRemoveItem}
        onMixMatch={onMixMatch}
        onPreview={onPreview}
        onSaveOutfit={onSaveOutfit}
        onShopOutfit={onShopOutfit}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  studioHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
    backgroundColor: "#ffffff",
  },
  studioTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  studioSubtitle: {
    fontSize: 11,
    color: "#888888",
    marginTop: 1,
  },
  topActionsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  resetButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  resetButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#6b7280",
  },
});
