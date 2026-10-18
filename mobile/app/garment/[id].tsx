import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
  Dimensions,
} from "react-native";
import { Image } from "expo-image";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useGarmentDetail } from "../../src/features/catalog/hooks";
import { useStartTryOn } from "../../src/features/tryon/useTryOn";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import { useBuy } from "../../src/features/commerce/useBuy";
import { Chip } from "../../src/components/Chip";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

export default function GarmentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { t } = useTranslation();
  const router = useRouter();

  const { data: garment, isLoading, isError, refetch } = useGarmentDetail(id || "");
  const { mutateAsync: startTryOn, isPending: isStartingTryOn } = useStartTryOn();
  const { mutate: saveToWardrobe, isPending: isSavingWardrobe } = useSaveToWardrobe();
  const { mutate: executeBuy, isPending: isBuying } = useBuy();

  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [tryOnError, setTryOnError] = useState<string | null>(null);

  const handleTryOn = async () => {
    if (!id || !garment?.tryon_supported) return;
    setTryOnError(null);
    try {
      const res = await startTryOn({ garmentId: id });
      router.push(`/tryon/${res.job_id}`);
    } catch (err: any) {
      setTryOnError(err?.detail || err?.message || "Failed to start try-on");
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (isError || !garment) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error")}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const images = garment.images && garment.images.length > 0 ? garment.images : [];
  const primaryOffer = garment.offers && garment.offers.length > 0 ? garment.offers[0] : null;
  const formattedPrice = `₹${(garment.price_minor / 100).toFixed(0)}`;

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Image Gallery */}
        <View style={styles.galleryContainer}>
          {images.length > 0 ? (
            <ScrollView
              horizontal
              pagingEnabled
              showsHorizontalScrollIndicator={false}
              onScroll={(e) => {
                const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
                setActiveImageIndex(idx);
              }}
              scrollEventThrottle={16}
            >
              {images.map((imgUrl, idx) => (
                <Image
                  key={idx}
                  source={{ uri: imgUrl, cacheKey: imgUrl.split("?")[0] }}
                  style={styles.galleryImage}
                  contentFit="cover"
                  transition={200}
                />
              ))}
            </ScrollView>
          ) : (
            <View style={styles.placeholderContainer}>
              <Text style={styles.placeholderIcon}>👗</Text>
            </View>
          )}

          {images.length > 1 && (
            <View style={styles.paginationDots}>
              {images.map((_, idx) => (
                <View
                  key={idx}
                  style={[
                    styles.dot,
                    activeImageIndex === idx ? styles.activeDot : null,
                  ]}
                />
              ))}
            </View>
          )}

          {garment.tryon_supported && (
            <View style={styles.tryonBadge}>
              <Text style={styles.tryonBadgeText}>✨ {t("feed.tryonBadge")}</Text>
            </View>
          )}
        </View>

        {/* Garment Metadata */}
        <View style={styles.infoContainer}>
          {garment.brand_name && (
            <Text style={styles.brandText}>{garment.brand_name.toUpperCase()}</Text>
          )}
          <Text style={styles.titleText}>{garment.title}</Text>
          <Text style={styles.priceText}>{formattedPrice}</Text>

          {/* Sizes in Stock */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t("garment.sizes")}</Text>
            {garment.sizes_in_stock && garment.sizes_in_stock.length > 0 ? (
              <View style={styles.chipsRow}>
                {garment.sizes_in_stock.map((size) => (
                  <Chip key={size} label={size} selected={false} />
                ))}
              </View>
            ) : (
              <Text style={styles.outOfStockText}>{t("garment.outOfStock")}</Text>
            )}
          </View>

          {/* Product Details */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{t("garment.details")}</Text>
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Category:</Text>
              <Text style={styles.detailValue}>{garment.category}</Text>
            </View>
            {garment.subcategory && (
              <View style={styles.detailRow}>
                <Text style={styles.detailLabel}>Subcategory:</Text>
                <Text style={styles.detailValue}>{garment.subcategory}</Text>
              </View>
            )}
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Gender:</Text>
              <Text style={styles.detailValue}>{garment.gender}</Text>
            </View>
          </View>

          {/* Affiliate Disclosure */}
          <View style={styles.disclosureBox}>
            <Text style={styles.disclosureText}>
              ℹ️ {t("garment.affiliateDisclosure")}
            </Text>
          </View>

          {tryOnError && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{tryOnError}</Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Action Footer */}
      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.saveButton}
          onPress={() => saveToWardrobe({ garmentId: garment.id })}
          disabled={isSavingWardrobe}
          accessibilityRole="button"
          accessibilityLabel={t("feed.save")}
        >
          <Text style={styles.saveButtonText}>
            {isSavingWardrobe ? "..." : "Save"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.buyButton}
          onPress={() => executeBuy(garment.id)}
          disabled={isBuying}
          accessibilityRole="button"
          accessibilityLabel={t("garment.buyNow")}
        >
          {isBuying ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Text style={styles.buyButtonText}>{t("garment.buyNow")}</Text>
          )}
        </TouchableOpacity>

        {/* Try-On Button: STRICTLY gated on tryon_supported */}
        {garment.tryon_supported ? (
          <TouchableOpacity
            style={[styles.tryOnButton, isStartingTryOn ? styles.buttonDisabled : null]}
            onPress={handleTryOn}
            disabled={isStartingTryOn}
            accessibilityRole="button"
            accessibilityLabel={t("garment.tryonButton")}
          >
            {isStartingTryOn ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.tryOnButtonText}>✨ {t("garment.tryonButton")}</Text>
            )}
          </TouchableOpacity>
        ) : (
          <View style={styles.tryonUnavailableBox}>
            <Text style={styles.tryonUnavailableText}>
              {t("garment.tryonUnavailable")}
            </Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  scrollContent: {
    paddingBottom: 110,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  galleryContainer: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 1.25,
    backgroundColor: "#F3F4F6",
    position: "relative",
  },
  galleryImage: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH * 1.25,
  },
  placeholderContainer: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderIcon: {
    fontSize: 72,
  },
  paginationDots: {
    position: "absolute",
    bottom: 16,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "rgba(255, 255, 255, 0.5)",
  },
  activeDot: {
    width: 18,
    backgroundColor: "#FFFFFF",
  },
  tryonBadge: {
    position: "absolute",
    top: 16,
    left: 16,
    backgroundColor: "rgba(17, 24, 39, 0.85)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  tryonBadgeText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  infoContainer: {
    padding: 20,
  },
  brandText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#6B7280",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  titleText: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111827",
    lineHeight: 28,
    marginBottom: 8,
  },
  priceText: {
    fontSize: 22,
    fontWeight: "800",
    color: "#111827",
    marginBottom: 20,
  },
  section: {
    marginBottom: 20,
    borderTopWidth: 1,
    borderTopColor: "#F3F4F6",
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 10,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  outOfStockText: {
    fontSize: 14,
    color: "#EF4444",
  },
  detailRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
  },
  detailLabel: {
    fontSize: 14,
    color: "#6B7280",
  },
  detailValue: {
    fontSize: 14,
    fontWeight: "500",
    color: "#111827",
    textTransform: "capitalize",
  },
  disclosureBox: {
    backgroundColor: "#F9FAFB",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginTop: 10,
  },
  disclosureText: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 18,
  },
  errorBox: {
    backgroundColor: "#FEF2F2",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FECACA",
    marginTop: 12,
  },
  errorBoxText: {
    color: "#DC2626",
    fontSize: 13,
  },
  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    elevation: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  saveButton: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
  },
  buyButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: "#111827",
    justifyContent: "center",
    alignItems: "center",
  },
  buyButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
  tryOnButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    backgroundColor: "#4F46E5",
    justifyContent: "center",
    alignItems: "center",
  },
  tryOnButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  tryonUnavailableBox: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  tryonUnavailableText: {
    fontSize: 12,
    color: "#9CA3AF",
    textAlign: "center",
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
