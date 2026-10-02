import React, { useState } from "react";
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { LookItemLinkContract, LookHotspotContract } from "../types";

interface LookDetailViewProps {
  heroImageUri: string;
  lookTitle: string;
  styleName: string;
  contextDescription: string;
  outfitItems: LookItemLinkContract[];
  hotspots?: LookHotspotContract[];
  onSelectProduct?: (productId: string) => void;
  onSaveLook?: () => void;
  isSaved?: boolean;
  testID?: string;
}

export const LookDetailView: React.FC<LookDetailViewProps> = ({
  heroImageUri,
  lookTitle,
  styleName,
  contextDescription,
  outfitItems = [],
  hotspots = [],
  onSelectProduct,
  onSaveLook,
  isSaved = false,
  testID = "look-detail-view",
}) => {
  const [activeHotspotId, setActiveHotspotId] = useState<string | null>(null);

  return (
    <View testID={testID} style={styles.container}>
      {/* Hero Look Image with Hotspots (Section 9.38 & 9.39) */}
      <View style={styles.heroContainer}>
        <Image
          source={{ uri: heroImageUri }}
          style={styles.heroImage}
          resizeMode="cover"
        />

        {/* Hotspots */}
        {hotspots.map((spot, idx) => {
          const isActive = spot.product_id === activeHotspotId;
          return (
            <TouchableOpacity
              key={`spot-${idx}`}
              testID={`${testID}-hotspot-${idx}`}
              onPress={() =>
                setActiveHotspotId(isActive ? null : spot.product_id)
              }
              style={[
                styles.hotspotPin,
                { left: `${spot.x_percent}%`, top: `${spot.y_percent}%` },
                isActive && styles.hotspotPinActive,
              ]}
              accessibilityRole="button"
              accessibilityLabel={`Hotspot for ${spot.label}`}
            >
              <View style={styles.pinDot} />
              {isActive && (
                <View style={styles.pinTooltip}>
                  <Text style={styles.pinTooltipText}>{spot.label}</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Look Metadata */}
      <View style={styles.metadataContainer}>
        <View style={styles.titleRow}>
          <View style={styles.titleWrapper}>
            <Text style={styles.styleBadge}>{styleName.toUpperCase()}</Text>
            <Text style={styles.lookTitle}>{lookTitle}</Text>
          </View>
          {onSaveLook && (
            <TouchableOpacity
              testID={`${testID}-save-button`}
              onPress={onSaveLook}
              style={[styles.saveButton, isSaved && styles.saveButtonActive]}
              accessibilityRole="button"
              accessibilityLabel={isSaved ? "Saved" : "Save Look"}
            >
              <Text style={[styles.saveButtonText, isSaved && styles.saveButtonTextActive]}>
                {isSaved ? "Saved ✓" : "Save Look"}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.contextText}>{contextDescription}</Text>
      </View>

      {/* Constituent Outfit Items List (Section 9.38) */}
      {outfitItems.length > 0 && (
        <View style={styles.itemsSection}>
          <Text style={styles.itemsSectionHeading}>Shoppable Look Pieces ({outfitItems.length})</Text>
          <View style={styles.itemsList}>
            {outfitItems.map((item) => (
              <TouchableOpacity
                key={item.product_id}
                testID={`${testID}-outfit-item-${item.product_id}`}
                onPress={() => onSelectProduct && onSelectProduct(item.product_id)}
                style={styles.itemCard}
                accessibilityRole="button"
                accessibilityLabel={`${item.slot}: ${item.title} by ${item.brand}, ₹${item.price}`}
              >
                <Image
                  source={{ uri: item.image_uri }}
                  style={styles.itemImage}
                  resizeMode="cover"
                />
                <View style={styles.itemContent}>
                  <Text style={styles.itemSlot}>{item.slot.toUpperCase()}</Text>
                  <Text style={styles.itemTitle} numberOfLines={1}>
                    {item.title}
                  </Text>
                  <Text style={styles.itemBrand}>{item.brand}</Text>
                  <Text style={styles.itemPrice}>₹{item.price.toLocaleString()}</Text>
                </View>
                <View style={styles.actionArrow}>
                  <Text style={styles.arrowText}>→</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#ffffff",
  },
  heroContainer: {
    width: "100%",
    aspectRatio: 3 / 4,
    backgroundColor: "#f5f5f5",
    position: "relative",
  },
  heroImage: {
    width: "100%",
    height: "100%",
  },
  hotspotPin: {
    position: "absolute",
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "rgba(255, 255, 255, 0.85)",
    justifyContent: "center",
    alignItems: "center",
    transform: [{ translateX: -13 }, { translateY: -13 }],
    borderWidth: 2,
    borderColor: "#111111",
    zIndex: 10,
  },
  hotspotPinActive: {
    backgroundColor: "#111111",
    borderColor: "#ffffff",
  },
  pinDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#111111",
  },
  pinTooltip: {
    position: "absolute",
    bottom: 30,
    backgroundColor: "rgba(0,0,0,0.85)",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    minWidth: 80,
    alignItems: "center",
  },
  pinTooltipText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "600",
  },
  metadataContainer: {
    padding: 16,
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  titleWrapper: {
    flex: 1,
    marginRight: 12,
  },
  styleBadge: {
    fontSize: 11,
    fontWeight: "700",
    color: "#666666",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  lookTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111111",
  },
  saveButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: "#111111",
  },
  saveButtonActive: {
    backgroundColor: "#111111",
  },
  saveButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111111",
  },
  saveButtonTextActive: {
    color: "#ffffff",
  },
  contextText: {
    fontSize: 14,
    color: "#555555",
    lineHeight: 20,
  },
  itemsSection: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
  itemsSectionHeading: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111111",
    marginBottom: 12,
  },
  itemsList: {
    gap: 10,
  },
  itemCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 10,
    backgroundColor: "#fafafa",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#eeeeee",
  },
  itemImage: {
    width: 60,
    height: 80,
    borderRadius: 4,
    backgroundColor: "#f0f0f0",
  },
  itemContent: {
    flex: 1,
    marginLeft: 12,
  },
  itemSlot: {
    fontSize: 10,
    fontWeight: "700",
    color: "#777777",
    letterSpacing: 0.5,
  },
  itemTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111111",
    marginVertical: 2,
  },
  itemBrand: {
    fontSize: 12,
    color: "#666666",
  },
  itemPrice: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111111",
    marginTop: 2,
  },
  actionArrow: {
    paddingHorizontal: 8,
  },
  arrowText: {
    fontSize: 16,
    color: "#888888",
  },
});
