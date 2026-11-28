import React, { useMemo } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import * as Linking from "expo-linking";
import { ApiError } from "../../src/api/errors";
import { ProductGallery } from "../../src/features/product-detail/components/ProductGallery";
import {
  useMerchantRedirect,
  useProductDetail,
} from "../../src/features/product-detail/hooks";
import {
  availabilityMessage,
  canPurchase,
} from "../../src/features/product-detail/utils/availability";
import { formatMinorPrice } from "../../src/features/product-detail/utils/formatPrice";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";

function ErrorMessage({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <View style={styles.center}>
      <Text style={styles.errorText}>{message}</Text>
      <Pressable onPress={onRetry} accessibilityRole="button">
        <Text style={styles.retryLink}>Try again</Text>
      </Pressable>
    </View>
  );
}

export default function ProductDetailScreen() {
  const params = useLocalSearchParams<{ productId: string; offerId?: string }>();
  const productId = String(params.productId ?? "");
  const offerId = String(params.offerId ?? "");

  const query = useProductDetail(productId, offerId);
  const { refetch } = query;
  const saveMutation = useSaveToWardrobe();
  const redirectMutation = useMerchantRedirect();

  const product = query.data;

  const price = useMemo(() => {
    if (!product) return "";
    return formatMinorPrice(product.price.amount_minor, product.price.currency);
  }, [product]);

  async function onSave() {
    if (!product || saveMutation.isPending) return;
    try {
      await saveMutation.mutateAsync({
        garmentId: product.garment_id,
        offerId: product.offer_id,
      });
      Alert.alert("Saved", "Added to your wardrobe.");
    } catch {
      Alert.alert("Could not save", "Please try again.");
    }
  }

  async function onMerchantRedirect() {
    if (!product?.permissions.redirect_allowed) {
      Alert.alert("Unavailable", "This merchant link is not currently available.");
      return;
    }

    try {
      const result = await redirectMutation.mutateAsync(product.offer_id);
      const parsed = Linking.parse(result.redirect_url);
      if (parsed.scheme !== "https" || !parsed.hostname) {
        throw new Error("Invalid merchant redirect URL");
      }
      await Linking.openURL(result.redirect_url);
    } catch {
      Alert.alert(
        "Merchant link unavailable",
        "The merchant link could not be opened. Refresh the product and try again.",
      );
    }
  }

  if (query.isPending) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text>Loading product...</Text>
      </View>
    );
  }

  if (query.isError) {
    const status = query.error instanceof ApiError ? query.error.status : 0;
    if (status === 404) {
      return (
        <ErrorMessage
          message="This product could not be found."
          onRetry={() => {
            void query.refetch();
          }}
        />
      );
    }
    if (status === 403) {
      return (
        <ErrorMessage
          message="This product is not available to view."
          onRetry={() => {
            void query.refetch();
          }}
        />
      );
    }
    return (
      <ErrorMessage
        message="We could not load this product. Check your connection and retry."
        onRetry={() => {
          void query.refetch();
        }}
      />
    );
  }

  if (!product) {
    return (
      <ErrorMessage
        message="Product details are unavailable."
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  const unavailable =
    product.availability === "delisted" || product.availability === "taken_down";

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <ProductGallery images={product.images} />

        <View style={styles.body}>
          <Text style={styles.title}>{product.title}</Text>
          <Text style={styles.meta}>
            {product.brand.name ?? "Brand not specified"}
          </Text>
          <Text style={styles.meta}>Sold by {product.merchant.name}</Text>
          <Text style={styles.price}>{price}</Text>

          {product.price.original_amount_minor != null &&
          product.price.original_amount_minor > product.price.amount_minor ? (
            <Text style={styles.meta}>
              Original price:{" "}
              {formatMinorPrice(
                product.price.original_amount_minor,
                product.price.currency,
              )}
            </Text>
          ) : null}

          <Text style={styles.availability}>
            {availabilityMessage(product.availability)}
          </Text>

          <Text style={styles.sectionTitle}>Available sizes</Text>
          {product.variants.length ? (
            <View style={styles.variantGrid}>
              {product.variants.map((variant) => (
                <View key={variant.id} style={styles.variantCard}>
                  <Text>{variant.size_label}</Text>
                  <Text style={styles.variantStatus}>
                    {availabilityMessage(variant.availability)}
                  </Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.meta}>Size information is not available.</Text>
          )}

          <Text style={styles.sectionTitle}>Product details</Text>
          {product.attributes.map((attribute) => (
            <View key={attribute.key} style={styles.attrRow}>
              <Text style={styles.meta}>{attribute.label}</Text>
              <Text style={styles.attrValue}>{attribute.value}</Text>
            </View>
          ))}

          {product.description ? <Text>{product.description}</Text> : null}

          <Text style={styles.disclaimer}>
            Product information is supplied by the merchant or identified catalog source. AI-enriched attributes are not merchant-certified.
          </Text>
        </View>
      </ScrollView>

      <View style={styles.actionBar}>
        <View style={styles.actionRow}>
          <Pressable
            disabled={unavailable || !product.permissions.vto_allowed}
            onPress={() =>
              router.push(`/garment/${product.garment_id}` as never)
            }
            style={[
              styles.primaryBtn,
              (unavailable || !product.permissions.vto_allowed) &&
                styles.disabledBtn,
            ]}
            accessibilityRole="button"
          >
            <Text style={styles.primaryBtnText}>Try it on</Text>
          </Pressable>

          <Pressable
            disabled={saveMutation.isPending}
            onPress={() => {
              void onSave();
            }}
            style={styles.secondaryBtn}
            accessibilityRole="button"
          >
            <Text>{saveMutation.isPending ? "Saving..." : "Save"}</Text>
          </Pressable>
        </View>

        <Pressable
          disabled={
            unavailable ||
            !canPurchase(product.availability) ||
            !product.permissions.redirect_allowed ||
            redirectMutation.isPending
          }
          onPress={() => {
            void onMerchantRedirect();
          }}
          style={styles.merchantBtn}
          accessibilityRole="button"
        >
          <Text>
            {redirectMutation.isPending
              ? "Opening merchant..."
              : "Continue to merchant"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#FFFFFF" },
  scrollContent: { paddingBottom: 130 },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 12 },
  errorText: { fontSize: 15, color: "#111827", textAlign: "center" },
  retryLink: { color: "#2563EB", fontWeight: "600" },
  body: { padding: 18, gap: 10 },
  title: { fontSize: 22, fontWeight: "700", color: "#111827" },
  meta: { color: "#6B7280", fontSize: 13 },
  price: { fontSize: 22, fontWeight: "700", color: "#111827" },
  availability: { fontSize: 14, fontWeight: "600", color: "#374151" },
  sectionTitle: { fontSize: 17, fontWeight: "600", marginTop: 8, color: "#111827" },
  variantGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  variantCard: {
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 8,
    padding: 10,
  },
  variantStatus: { fontSize: 10, color: "#6B7280" },
  attrRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
  },
  attrValue: { flex: 1, textAlign: "right", color: "#111827" },
  disclaimer: { fontSize: 11, color: "#6B7280", marginTop: 8 },
  actionBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
    gap: 8,
  },
  actionRow: { flexDirection: "row", gap: 8 },
  primaryBtn: {
    flex: 1,
    padding: 14,
    backgroundColor: "#111827",
    borderRadius: 10,
    alignItems: "center",
  },
  disabledBtn: { backgroundColor: "#9CA3AF" },
  primaryBtnText: { color: "#FFFFFF", fontWeight: "600" },
  secondaryBtn: {
    flex: 1,
    padding: 14,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 10,
    alignItems: "center",
  },
  merchantBtn: {
    padding: 14,
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    alignItems: "center",
  },
});
