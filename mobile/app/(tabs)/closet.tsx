import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Alert,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  useCloset,
  useRemoveItem,
  useMarkPurchased,
  useFitFeedback,
  ClosetItem,
  FitVerdict,
} from "../../src/features/wardrobe/hooks";
import { useBuy } from "../../src/features/commerce/useBuy";
import { fitCardDue, priceNote } from "../../src/features/wardrobe/logic";
import { useAuthStore } from "../../src/features/auth/authStore";
import { useSignedImage } from "../../src/hooks/useSignedImage";

function RenderImage({ render }: { render: { url: string; expires_at: number } }) {
  const { uri } = useSignedImage({
    url: render.url,
    expiresAt: render.expires_at,
  });

  if (!uri) {
    return (
      <View style={styles.imageLoading}>
        <ActivityIndicator size="small" color="#4F46E5" />
      </View>
    );
  }

  return (
    <Image
      source={{ uri }}
      style={styles.cardImage}
      contentFit="cover"
      accessibilityLabel="Try-on render"
    />
  );
}

function ClosetCardItem({
  item,
  onRemove,
  onMarkPurchased,
  onFitFeedback,
  onBuy,
  isBuying,
}: {
  item: ClosetItem;
  onRemove: (id: string) => void;
  onMarkPurchased: (id: string) => void;
  onFitFeedback: (itemId: string, verdict: FitVerdict) => void;
  onBuy: (garmentId: string) => void;
  isBuying: boolean;
}) {
  const { t } = useTranslation();
  const router = useRouter();
  const [feedbackAnswered, setFeedbackAnswered] = useState(false);

  const itemId = item.id || item.item_id || "";
  const isFitDue = !feedbackAnswered && fitCardDue(item);
  const note = priceNote({
    price_at_save: item.price_at_save ?? item.snapshot_price_minor ?? 0,
    current_price: item.current_price,
  });
  const savedPriceMinor = item.price_at_save ?? item.snapshot_price_minor ?? 0;
  const savedPriceFormatted = `₹${(savedPriceMinor / 100).toFixed(0)}`;
  const title = item.title_at_save || item.snapshot_title || t("closet.saved_item", "Saved Item");

  const handleRemove = () => {
    Alert.alert(
      t("closet.remove_confirm_title", "Remove item"),
      t("closet.remove_confirm_msg", "Are you sure you want to remove this item from your closet?"),
      [
        { text: t("common.cancel", "Cancel"), style: "cancel" },
        {
          text: t("common.remove", "Remove"),
          style: "destructive",
          onPress: () => onRemove(itemId),
        },
      ]
    );
  };

  const handleVerdict = (verdict: FitVerdict) => {
    setFeedbackAnswered(true);
    onFitFeedback(itemId, verdict);
  };

  return (
    <View style={styles.card} accessibilityRole="none">
      {/* 1. Fit Feedback Card (when due) */}
      {isFitDue && (
        <View style={styles.fitCard} testID="fit-feedback-card">
          <Text style={styles.fitCardTitle}>
            {t("closet.fit_question", "How did it fit?")}
          </Text>
          <View style={styles.fitButtonRow}>
            <TouchableOpacity
              style={styles.fitButton}
              onPress={() => handleVerdict("too_tight")}
              accessibilityRole="button"
              accessibilityLabel={t("closet.too_small", "Too small")}
            >
              <Text style={styles.fitButtonText}>{t("closet.too_small", "Too small")}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.fitButton, styles.fitButtonPrimary]}
              onPress={() => handleVerdict("true_to_size")}
              accessibilityRole="button"
              accessibilityLabel={t("closet.true_to_size", "True to size")}
            >
              <Text style={[styles.fitButtonText, styles.fitButtonPrimaryText]}>
                {t("closet.true_to_size", "True to size")}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.fitButton}
              onPress={() => handleVerdict("too_loose")}
              accessibilityRole="button"
              accessibilityLabel={t("closet.too_large", "Too large")}
            >
              <Text style={styles.fitButtonText}>{t("closet.too_large", "Too large")}</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* 2. Visual or Clean Text Card */}
      {item.render ? (
        <TouchableOpacity
          activeOpacity={0.9}
          onPress={() => router.push(`/garment/${item.garment_id}`)}
          accessibilityRole="button"
          accessibilityLabel={`View garment ${title}`}
        >
          <RenderImage render={item.render} />
        </TouchableOpacity>
      ) : (
        <TouchableOpacity
          style={styles.textCardContainer}
          activeOpacity={0.8}
          onPress={() => router.push(`/garment/${item.garment_id}`)}
          accessibilityRole="button"
          accessibilityLabel={`View garment ${title}`}
          testID="text-card-fallback"
        >
          <Text style={styles.textCardBadge}>{t("closet.saved_look", "SAVED LOOK")}</Text>
          <Text style={styles.textCardTitle} numberOfLines={2}>
            {title}
          </Text>
        </TouchableOpacity>
      )}

      {/* 3. Details & Price */}
      <View style={styles.detailsContainer}>
        <Text style={styles.itemTitle} numberOfLines={1}>
          {title}
        </Text>

        <View style={styles.priceContainer}>
          <Text style={styles.savedPrice}>
            {t("closet.saved_at", "Saved at {{price}}", { price: savedPriceFormatted })}
          </Text>
          {note && (
            <Text style={styles.priceNote} testID="price-note">
              {t("closet.now_at", " · now ₹{{price}}", { price: (note.now / 100).toFixed(0) })}
            </Text>
          )}
        </View>

        {/* 4. Actions: Buy, Mark Purchased, Remove */}
        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={[styles.buyButton, isBuying && styles.buttonDisabled]}
            disabled={isBuying}
            onPress={() => onBuy(item.garment_id)}
            accessibilityRole="button"
            accessibilityLabel={t("closet.buy_now", "Buy")}
          >
            {isBuying ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <Text style={styles.buyButtonText}>{t("closet.buy_now", "Buy")}</Text>
            )}
          </TouchableOpacity>

          {!item.purchased_at ? (
            <TouchableOpacity
              style={styles.purchasedButton}
              onPress={() => onMarkPurchased(itemId)}
              accessibilityRole="button"
              accessibilityLabel={t("closet.i_bought_this", "I bought this")}
            >
              <Text style={styles.purchasedButtonText}>
                {t("closet.i_bought_this", "I bought this")}
              </Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.purchasedBadge}>
              <Text style={styles.purchasedBadgeText}>
                ✓ {t("closet.purchased", "Purchased")}
              </Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.removeButton}
            onPress={handleRemove}
            accessibilityRole="button"
            accessibilityLabel={t("common.remove", "Remove")}
          >
            <Text style={styles.removeButtonText}>{t("common.remove", "Remove")}</Text>
          </TouchableOpacity>
        </View>

        {/* 5. Commission disclosure */}
        <Text style={styles.commissionDisclosure}>
          {t(
            "closet.commission_notice",
            "We may earn a commission if you buy through this link"
          )}
        </Text>
      </View>
    </View>
  );
}

export default function ClosetScreen() {
  const { t } = useTranslation();
  const me = useAuthStore((s) => s.me);
  const { data: wardrobeItems, isLoading, isError, refetch, isRefetching } = useCloset(me?.user_id);
  const removeMutation = useRemoveItem();
  const markPurchasedMutation = useMarkPurchased();
  const fitFeedbackMutation = useFitFeedback();
  const buyMutation = useBuy();

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error", "Something went wrong")}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>{t("common.retry", "Retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={wardrobeItems || []}
        renderItem={({ item }) => (
          <ClosetCardItem
            item={item}
            onRemove={(id) => removeMutation.mutate(id)}
            onMarkPurchased={(id) => markPurchasedMutation.mutate(id)}
            onFitFeedback={(itemId, verdict) => fitFeedbackMutation.mutate({ item_id: itemId, verdict })}
            onBuy={(garmentId) => buyMutation.mutate(garmentId)}
            isBuying={buyMutation.isPending}
          />
        )}
        keyExtractor={(item) => item.id || item.item_id || item.garment_id}
        refreshing={isRefetching}
        onRefresh={refetch}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>👗</Text>
            <Text style={styles.emptyTitle}>
              {t("closet.empty_title", "Your closet is empty")}
            </Text>
            <Text style={styles.emptySub}>
              {t(
                "closet.empty_subtitle",
                "Save looks from the feed or try-ons to build your personal collection."
              )}
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  listContent: {
    padding: 16,
    gap: 16,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    marginBottom: 12,
  },
  fitCard: {
    backgroundColor: "#EEF2FF",
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#E0E7FF",
  },
  fitCardTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#3730A3",
    marginBottom: 8,
    textAlign: "center",
  },
  fitButtonRow: {
    flexDirection: "row",
    gap: 8,
    justifyContent: "center",
  },
  fitButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#C7D2FE",
  },
  fitButtonPrimary: {
    backgroundColor: "#4F46E5",
    borderColor: "#4F46E5",
  },
  fitButtonText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#4338CA",
  },
  fitButtonPrimaryText: {
    color: "#FFFFFF",
  },
  cardImage: {
    width: "100%",
    height: 320,
    backgroundColor: "#F3F4F6",
  },
  imageLoading: {
    width: "100%",
    height: 320,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
  },
  textCardContainer: {
    width: "100%",
    padding: 28,
    backgroundColor: "#F8FAFC",
    borderBottomWidth: 1,
    borderBottomColor: "#E2E8F0",
    alignItems: "center",
  },
  textCardBadge: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.2,
    color: "#64748B",
    marginBottom: 8,
  },
  textCardTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1E293B",
    textAlign: "center",
  },
  detailsContainer: {
    padding: 16,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  priceContainer: {
    flexDirection: "row",
    alignItems: "baseline",
    marginBottom: 12,
  },
  savedPrice: {
    fontSize: 14,
    fontWeight: "500",
    color: "#4B5563",
  },
  priceNote: {
    fontSize: 14,
    fontWeight: "700",
    color: "#059669",
  },
  actionsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  buyButton: {
    backgroundColor: "#111827",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    minHeight: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buyButtonText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  purchasedButton: {
    backgroundColor: "#F3F4F6",
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    minHeight: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  purchasedButtonText: {
    color: "#374151",
    fontSize: 13,
    fontWeight: "600",
  },
  purchasedBadge: {
    backgroundColor: "#DCFCE7",
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  purchasedBadgeText: {
    color: "#15803D",
    fontSize: 12,
    fontWeight: "600",
  },
  removeButton: {
    marginLeft: "auto",
    paddingVertical: 10,
    paddingHorizontal: 8,
  },
  removeButtonText: {
    color: "#EF4444",
    fontSize: 13,
    fontWeight: "500",
  },
  commissionDisclosure: {
    fontSize: 11,
    color: "#6B7280",
    fontStyle: "italic",
    marginTop: 4,
  },
  emptyContainer: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 64,
    paddingHorizontal: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 8,
  },
  emptySub: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 20,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#EF4444",
    marginBottom: 12,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
