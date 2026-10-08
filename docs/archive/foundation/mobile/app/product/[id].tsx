import React, { useMemo, useState } from "react";
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import { useCatalogActions, useProductDetail } from "../../features/product/useProductDetail";

function priceLabel(minor: number, currency: string): string {
  return `${currency} ${(minor / 100).toFixed(0)}`;
}

export default function ProductDetailScreen() {
  const params = useLocalSearchParams<{ id: string; offerId?: string }>();
  const router = useRouter();
  const productId = String(params.id);
  const [selectedOfferId, setSelectedOfferId] = useState<string | undefined>(params.offerId);
  const detail = useProductDetail(productId, selectedOfferId);
  const actions = useCatalogActions(productId);

  const selectedOffer = useMemo(
    () => detail.data?.offers.find((offer) => offer.id === (selectedOfferId ?? detail.data?.selected_offer_id)),
    [detail.data, selectedOfferId],
  );

  if (detail.isPending) {
    return <View style={styles.center}><Text>Loading product…</Text></View>;
  }

  if (detail.isError || !detail.data) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>Unable to load this product.</Text>
        <Pressable style={styles.primaryButton} onPress={() => void detail.refetch()}>
          <Text style={styles.primaryText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const garment = detail.data.garment;
  const hero = detail.data.images.find((image) => image.image_type === "front") ?? detail.data.images[0];

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()}><Text style={styles.back}>Back</Text></Pressable>
      <View style={styles.hero}>
        {hero?.url ? <Image source={{ uri: hero.url }} style={styles.heroImage} /> : <Text style={styles.placeholder}>Product image unavailable</Text>}
      </View>
      <Text style={styles.title}>{garment.display_name}</Text>
      <Text style={styles.meta}>{garment.category}{garment.subcategory ? ` · ${garment.subcategory}` : ""}</Text>

      <Text style={styles.sectionTitle}>Available offers</Text>
      {detail.data.offers.map((offer) => (
        <Pressable
          key={offer.id}
          style={[styles.offer, offer.id === (selectedOfferId ?? detail.data?.selected_offer_id) && styles.offerSelected]}
          onPress={() => setSelectedOfferId(offer.id)}
          disabled={!offer.in_stock}
        >
          <View style={styles.offerText}>
            <Text style={styles.offerPrice}>{priceLabel(offer.price_minor, offer.currency)}</Text>
            <Text style={styles.offerMeta}>{offer.in_stock ? "In stock" : "Unavailable"}</Text>
          </View>
          <Text>{offer.in_stock ? "Select" : "Unavailable"}</Text>
        </Pressable>
      ))}

      {selectedOffer && <Text style={styles.selected}>Selected offer: {priceLabel(selectedOffer.price_minor, selectedOffer.currency)}</Text>}

      <Pressable
        style={styles.tryOnButton}
        onPress={() => router.push({ pathname: "/tryon/[productId]", params: { productId } })}
      >
        <Text style={styles.tryOnText}>Try On This Garment</Text>
      </Pressable>
      <View style={styles.actions}>
        <Pressable
          style={styles.primaryButton}
          onPress={() => void actions.save.mutateAsync(selectedOfferId ?? detail.data.selected_offer_id ?? undefined)}
          disabled={actions.save.isPending}
        >
          <Text style={styles.primaryText}>{actions.save.isPending ? "Saving…" : "Save"}</Text>
        </Pressable>
        <Pressable
          style={styles.secondaryButton}
          onPress={async () => {
            await actions.reject.mutateAsync();
            router.back();
          }}
          disabled={actions.reject.isPending}
        >
          <Text style={styles.secondaryText}>Not for me</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12 },
  back: { fontSize: 16, fontWeight: "600", marginBottom: 4 },
  hero: { height: 420, borderRadius: 18, backgroundColor: "#f3f4f6", alignItems: "center", justifyContent: "center", overflow: "hidden" },
  heroImage: { width: "100%", height: "100%" },
  placeholder: { color: "#6b7280" },
  title: { fontSize: 24, fontWeight: "700", marginTop: 8 },
  meta: { color: "#6b7280" },
  sectionTitle: { marginTop: 16, fontSize: 18, fontWeight: "700" },
  offer: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 14, borderRadius: 14, borderWidth: 1, borderColor: "#e5e7eb" },
  offerSelected: { borderColor: "#111827" },
  offerText: { gap: 3 },
  offerPrice: { fontWeight: "700", fontSize: 16 },
  offerMeta: { color: "#6b7280" },
  selected: { fontWeight: "600" },
  tryOnButton: { minHeight: 52, borderRadius: 12, backgroundColor: "#2563eb", alignItems: "center", justifyContent: "center", marginTop: 12 },
  tryOnText: { color: "#ffffff", fontWeight: "800" },
  actions: { flexDirection: "row", gap: 10, marginTop: 12 },
  primaryButton: { flex: 1, backgroundColor: "#111827", borderRadius: 12, padding: 14, alignItems: "center" },
  primaryText: { color: "#ffffff", fontWeight: "700" },
  secondaryButton: { flex: 1, borderWidth: 1, borderColor: "#d1d5db", borderRadius: 12, padding: 14, alignItems: "center" },
  secondaryText: { fontWeight: "700" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  error: { marginBottom: 12 },
});
