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
  merchant_id?: string;
  merchant_name?: string | null;
  price_minor: number;
  currency: string;
  in_stock: boolean;
  updated_at?: string | null;
};

export type Props = {
  garmentId?: string;
  offers: RetailerOffer[];
  onBuy?: (offerId: string) => void;
  isBuying?: boolean;
};

export function formatOfferPrice(amountMinor: number, currency: string): string {
  const major = amountMinor / 100;
  if (currency.toUpperCase() === "INR") {
    return major % 1 === 0 ? `₹${major.toFixed(0)}` : `₹${major.toFixed(2)}`;
  }
  if (currency.toUpperCase() === "USD") {
    return `$${major.toFixed(2)}`;
  }
  if (currency.toUpperCase() === "EUR") {
    return `€${major.toFixed(2)}`;
  }
  return `${currency.toUpperCase()} ${major.toFixed(2)}`;
}

export function RetailerOffers({ garmentId, offers, onBuy, isBuying: externalIsBuying }: Props) {
  const [selectedOfferId, setSelectedOfferId] = useState<string | null>(null);

  const buyClickMutation = useCreateBuyClick();
  const isBuying = Boolean(externalIsBuying || buyClickMutation.isPending);

  const handleShop = async () => {
    if (!selectedOfferId || isBuying) return;

    if (onBuy) {
      onBuy(selectedOfferId);
      return;
    }

    if (!garmentId) return;

    try {
      const result = await buyClickMutation.mutateAsync({
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
    return (
      <View style={styles.container} accessibilityRole="summary">
        <Text style={styles.emptyText}>No retailer offers are currently available.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.heading} accessibilityRole="header">
        Compare retailer offers
      </Text>
      {offers.map((offer) => {
        const isSelected = selectedOfferId === offer.id;
        const merchantTitle = offer.merchant_name || "Authorized Retailer";

        return (
          <TouchableOpacity
            key={offer.id}
            disabled={!offer.in_stock || isBuying}
            onPress={() => setSelectedOfferId(offer.id)}
            style={[
              styles.offerRow,
              isSelected ? styles.offerRowSelected : null,
              !offer.in_stock ? styles.offerRowDisabled : null,
            ]}
            accessibilityRole="radio"
            accessibilityLabel={`${merchantTitle}, ${formatOfferPrice(offer.price_minor, offer.currency)}, ${
              offer.in_stock ? "In stock" : "Currently unavailable"
            }`}
            accessibilityState={{
              selected: isSelected,
              disabled: !offer.in_stock,
            }}
          >
            <View style={styles.offerInfo}>
              <View>
                <Text style={styles.merchantName}>{merchantTitle}</Text>
                <Text
                  style={[
                    styles.offerPrice,
                    !offer.in_stock ? styles.textDisabled : null,
                  ]}
                >
                  {formatOfferPrice(offer.price_minor, offer.currency)}
                </Text>
              </View>
              {!offer.in_stock && (
                <Text style={styles.outOfStockTag}>Currently unavailable</Text>
              )}
            </View>
            <View style={styles.selectActionBox}>
              <Text style={isSelected ? styles.selectedLabel : styles.selectLabel}>
                {isSelected ? "Selected" : "Select offer"}
              </Text>
              <Text
                style={[
                  styles.checkMark,
                  isSelected ? styles.checkMarkSelected : null,
                ]}
              >
                {isSelected ? "●" : "○"}
              </Text>
            </View>
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity
        onPress={handleShop}
        disabled={!selectedOfferId || isBuying}
        style={[
          styles.shopButton,
          !selectedOfferId || isBuying ? styles.shopButtonDisabled : null,
        ]}
        accessibilityRole="button"
        accessibilityLabel="Continue to selected retailer"
        accessibilityState={{
          disabled: !selectedOfferId || isBuying,
        }}
      >
        {isBuying ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color="#FFFFFF" />
            <Text style={styles.shopButtonText}>Preparing retailer link...</Text>
          </View>
        ) : (
          <Text style={styles.shopButtonText}>Continue to retailer</Text>
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
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
  },
  offerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 14,
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginBottom: 8,
  },
  offerRowSelected: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
    borderWidth: 2,
  },
  offerRowDisabled: {
    opacity: 0.5,
    backgroundColor: "#F3F4F6",
  },
  offerInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1,
  },
  merchantName: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4B5563",
    marginBottom: 2,
  },
  offerPrice: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111827",
  },
  outOfStockTag: {
    fontSize: 12,
    color: "#DC2626",
    fontWeight: "600",
    marginLeft: 8,
  },
  textDisabled: {
    color: "#9CA3AF",
  },
  selectActionBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  selectLabel: {
    fontSize: 13,
    color: "#6B7280",
    fontWeight: "500",
  },
  selectedLabel: {
    fontSize: 13,
    color: "#4F46E5",
    fontWeight: "700",
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
    marginTop: 10,
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  shopButtonDisabled: {
    backgroundColor: "#A5B4FC",
    opacity: 0.6,
  },
  shopButtonText: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 15,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
});
