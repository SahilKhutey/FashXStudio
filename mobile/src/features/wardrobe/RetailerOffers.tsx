import React, { useState } from "react";
import {
  Alert,
  Linking,
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  View,
} from "react-native";
import { useCreateBuyClick } from "./commerceHooks";
import { isSafeRetailerRedirect } from "../../lib/safeRedirect";

export type RetailerOffer = {
  id: string;
  price_minor: number;
  currency: string;
  in_stock: boolean;
};

type Props = {
  garmentId: string;
  offers: RetailerOffer[];
};

export function RetailerOffers({ garmentId, offers }: Props) {
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(null);

  const buyClick = useCreateBuyClick();

  const handleShop = async () => {
    if (!selectedOfferId || buyClick.isPending) return;

    try {
      const result = await buyClick.mutateAsync({
        garmentId,
        offerId: selectedOfferId,
      });

      if (!isSafeRetailerRedirect(result.redirect_url)) {
        throw new Error("Invalid or unsafe redirect URL");
      }
      await Linking.openURL(result.redirect_url);
    } catch {
      Alert.alert(
        "Unable to open retailer",
        "The shopping link could not be prepared. Please try again."
      );
    }
  };

  if (!offers || offers.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Available Retailer Offers</Text>
      {offers.map((offer) => {
        const isSelected = selectedOfferId === offer.id;
        return (
          <TouchableOpacity
            key={offer.id}
            disabled={!offer.in_stock}
            onPress={() => setSelectedOfferId(offer.id)}
            style={[
              styles.offerRow,
              isSelected ? styles.offerRowSelected : null,
              !offer.in_stock ? styles.offerRowDisabled : null,
            ]}
            accessibilityRole="radio"
            accessibilityState={{
              selected: isSelected,
              disabled: !offer.in_stock,
            }}
          >
            <View style={styles.offerInfo}>
              <Text
                style={[
                  styles.offerPrice,
                  !offer.in_stock ? styles.textDisabled : null,
                ]}
              >
                {offer.currency} {(offer.price_minor / 100).toFixed(2)}
              </Text>
              {!offer.in_stock && (
                <Text style={styles.outOfStockTag}>Out of stock</Text>
              )}
            </View>
            <Text
              style={[
                styles.checkMark,
                isSelected ? styles.checkMarkSelected : null,
              ]}
            >
              {isSelected ? "✓" : "○"}
            </Text>
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity
        onPress={handleShop}
        disabled={!selectedOfferId || buyClick.isPending}
        style={[
          styles.shopButton,
          !selectedOfferId || buyClick.isPending ? styles.shopButtonDisabled : null,
        ]}
        accessibilityRole="button"
      >
        {buyClick.isPending ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color="#FFFFFF" />
            <Text style={styles.shopButtonText}>Preparing retailer link...</Text>
          </View>
        ) : (
          <Text style={styles.shopButtonText}>Shop at retailer</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    padding: 16,
    backgroundColor: "#F9FAFB",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  heading: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 12,
  },
  offerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginBottom: 8,
  },
  offerRowSelected: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  offerRowDisabled: {
    opacity: 0.5,
  },
  offerInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  offerPrice: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1F2937",
  },
  outOfStockTag: {
    fontSize: 12,
    color: "#DC2626",
    fontWeight: "500",
  },
  textDisabled: {
    color: "#9CA3AF",
  },
  checkMark: {
    fontSize: 16,
    color: "#9CA3AF",
  },
  checkMarkSelected: {
    color: "#4F46E5",
    fontWeight: "bold",
  },
  shopButton: {
    marginTop: 8,
    backgroundColor: "#4F46E5",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  shopButtonDisabled: {
    backgroundColor: "#A5B4FC",
  },
  shopButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
    fontSize: 14,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
});
